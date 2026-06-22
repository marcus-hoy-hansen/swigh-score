#define _XOPEN_SOURCE 700
#define _GNU_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <ctype.h>
#include <unistd.h>
#include <stdint.h>
#include <sys/sysinfo.h>

#ifdef __linux__
#include <sched.h>
#endif

/* ---------------- Config ---------------- */
#ifndef MAX_QUEUE
#define MAX_QUEUE 8192
#endif

#ifndef DEFAULT_BATCH
#define DEFAULT_BATCH 256
#endif

#define SW_MATCH     2
#define SW_MISMATCH  1
#define SW_GAP       2

/* Uncomment to enable Linux thread pinning */
/* #define USE_AFFINITY 1 */

/* ---------------- Globals ---------------- */

static int g_sw_band = 0;   /* 0 = full SW, >0 = banded ±band */

/* ---------------- Task / Queue ---------------- */

typedef struct {
    size_t nlines;
    char **lines;
} task_t;

static task_t *queue_buf[MAX_QUEUE];
static size_t q_head = 0, q_tail = 0, q_count = 0;
static int producer_done = 0;

static pthread_mutex_t q_mtx = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t q_not_empty = PTHREAD_COND_INITIALIZER;
static pthread_cond_t q_not_full  = PTHREAD_COND_INITIALIZER;

static pthread_mutex_t out_mtx = PTHREAD_MUTEX_INITIALIZER;

/* ---------------- Utilities ---------------- */

static inline void chomp(char *s) {
    size_t n = strlen(s);
    while (n && (s[n-1] == '\n' || s[n-1] == '\r')) s[--n] = 0;
}

static inline void trim_left(char *s) {
    char *p = s;
    while (*p && isspace((unsigned char)*p)) ++p;
    if (p != s) memmove(s, p, strlen(p) + 1);
}

/* ---------------- Smith–Waterman ---------------- */

typedef struct {
    int *prev;
    int *curr;
    size_t cap;
} sw_buf_t;

/* ---- Full Smith–Waterman ---- */
static inline int
smith_waterman(const char *a, const char *b, sw_buf_t *buf)
{
    size_t n = strlen(a);
    size_t m = strlen(b);
    if (!n || !m) return 0;

    if (buf->cap < m + 1) {
        buf->prev = realloc(buf->prev, (m + 1) * sizeof(int));
        buf->curr = realloc(buf->curr, (m + 1) * sizeof(int));
        buf->cap  = m + 1;
    }
    memset(buf->prev, 0, (m + 1) * sizeof(int));

    int best = 0;

    for (size_t i = 1; i <= n; ++i) {
        int left = 0;
        char ca = a[i - 1];
        for (size_t j = 1; j <= m; ++j) {
            int match = (ca == b[j - 1]) ? SW_MATCH : -SW_MISMATCH;
            int diag  = buf->prev[j - 1] + match;
            int up    = buf->prev[j] - SW_GAP;
            int left_gap = left - SW_GAP;

            int h = diag > up ? diag : up;
            if (left_gap > h) h = left_gap;
            if (h < 0) h = 0;

            buf->curr[j] = h;
            left = h;
            if (h > best) best = h;
        }
        int *tmp = buf->prev;
        buf->prev = buf->curr;
        buf->curr = tmp;
    }
    return best;
}

/* ---- Banded Smith–Waterman ---- */
static inline int
smith_waterman_banded(const char *a, const char *b, sw_buf_t *buf, int band)
{
    size_t n = strlen(a);
    size_t m = strlen(b);
    if (!n || !m) return 0;

    if (buf->cap < m + 1) {
        buf->prev = realloc(buf->prev, (m + 1) * sizeof(int));
        buf->curr = realloc(buf->curr, (m + 1) * sizeof(int));
        buf->cap  = m + 1;
    }

    memset(buf->prev, 0, (m + 1) * sizeof(int));
    int best = 0;

    for (size_t i = 1; i <= n; ++i) {
        memset(buf->curr, 0, (m + 1) * sizeof(int));
        int left = 0;

        size_t j_start = (i > (size_t)band) ? i - band : 1;
        if (j_start > m) continue;
        size_t j_end   = (i + band < m)     ? i + band : m;

        char ca = a[i - 1];

        for (size_t j = j_start; j <= j_end; ++j) {
            int match = (ca == b[j - 1]) ? SW_MATCH : -SW_MISMATCH;
            int diag  = buf->prev[j - 1] + match;
            int up    = buf->prev[j] - SW_GAP;
            int left_gap = left - SW_GAP;

            int h = diag;
            if (up > h)        h = up;
            if (left_gap > h) h = left_gap;
            if (h < 0)        h = 0;

            buf->curr[j] = h;
            left = h;
            if (h > best) best = h;
        }

        int *tmp = buf->prev;
        buf->prev = buf->curr;
        buf->curr = tmp;
    }
    return best;
}

/* ---------------- Queue helpers ---------------- */

static void enqueue(task_t *t) {
    pthread_mutex_lock(&q_mtx);
    while (q_count == MAX_QUEUE)
        pthread_cond_wait(&q_not_full, &q_mtx);
    queue_buf[q_tail] = t;
    q_tail = (q_tail + 1) % MAX_QUEUE;
    q_count++;
    pthread_cond_signal(&q_not_empty);
    pthread_mutex_unlock(&q_mtx);
}

static task_t *dequeue(void) {
    pthread_mutex_lock(&q_mtx);
    while (q_count == 0 && !producer_done)
        pthread_cond_wait(&q_not_empty, &q_mtx);
    if (q_count == 0 && producer_done) {
        pthread_mutex_unlock(&q_mtx);
        return NULL;
    }
    task_t *t = queue_buf[q_head];
    q_head = (q_head + 1) % MAX_QUEUE;
    q_count--;
    pthread_cond_signal(&q_not_full);
    pthread_mutex_unlock(&q_mtx);
    return t;
}

/* ---------------- Worker ---------------- */

typedef struct {
    int tid;
    const char *ref;
    size_t ref_len;
} worker_arg_t;

static void *worker_main(void *arg) {
    worker_arg_t *wa = arg;

#ifdef USE_AFFINITY
#ifdef __linux__
    cpu_set_t set;
    CPU_ZERO(&set);
    CPU_SET(wa->tid % get_nprocs(), &set);
    pthread_setaffinity_np(pthread_self(), sizeof(set), &set);
#endif
#endif

    sw_buf_t sw = {0};
    const size_t ref_len = wa->ref_len;

    char *out = malloc(1 << 16);
    size_t olen = 0, ocap = 1 << 16;

    for (;;) {
        task_t *t = dequeue();
        if (!t) break;

        for (size_t i = 0; i < t->nlines; ++i) {
            char *q = t->lines[i];
            chomp(q);
            trim_left(q);
            if (*q) {
                size_t qlen = strlen(q);
                size_t min_len = qlen < ref_len ? qlen : ref_len;
                int score = (g_sw_band > 0)
                    ? smith_waterman_banded(q, wa->ref, &sw, g_sw_band)
                    : smith_waterman(q, wa->ref, &sw);

                /* Normalize by shortest sequence and match reward to mirror legacy percent */
                double sw_percent = 0.0;
                if (min_len > 0)
                    sw_percent = (double)score / (double)(min_len * SW_MATCH);
                double swighscore = sw_percent * ((double)score + (double)min_len);

                size_t need = strlen(q) + 64;
                while (olen + need > ocap) {
                    ocap *= 2;
                    out = realloc(out, ocap);
                }
                olen += snprintf(out + olen, ocap - olen,
                                 "%s\t%.6f\t%d\t%zu\t%.6f\n",
                                 q, sw_percent, score, min_len, swighscore);
            }
            free(q);
        }
        free(t->lines);
        free(t);
    }

    pthread_mutex_lock(&out_mtx);
    fwrite(out, 1, olen, stdout);
    pthread_mutex_unlock(&out_mtx);

    free(out);
    free(sw.prev);
    free(sw.curr);
    return NULL;
}

/* ---------------- Producer ---------------- */

static void produce(FILE *fp, size_t batch) {
    for (;;) {
        task_t *t = calloc(1, sizeof(*t));
        t->lines = calloc(batch, sizeof(char*));
        size_t n = 0;

        for (; n < batch; ++n) {
            char *line = NULL;
            size_t cap = 0;
            if (getline(&line, &cap, fp) < 0) {
                free(line);
                break;
            }
            t->lines[n] = line;
        }

        if (n == 0) {
            free(t->lines);
            free(t);
            break;
        }
        t->nlines = n;
        enqueue(t);
        if (n < batch) break;
    }

    pthread_mutex_lock(&q_mtx);
    producer_done = 1;
    pthread_cond_broadcast(&q_not_empty);
    pthread_mutex_unlock(&q_mtx);
}

/* ---------------- Main ---------------- */

static void usage(const char *prog) {
    fprintf(stderr,
      "Usage:\n"
      "  %s -r <ref> -i <reads.txt|-> [-t threads] [-B batch] [-b band]\n"
      "  %s <REF> <reads.txt|-> [threads] [batch] [band]   (positional)\n"
      "  band = 0 (default) → full Smith–Waterman\n"
      "  band > 0           → banded ±band\n"
      "Output columns match the legacy SWscore tool:\n"
      "  <read>\t<similarity>\t<SW score>\t<aligned bases>\t<swigh-score>\n",
      prog, prog);
}

int main(int argc, char **argv) {
    const char *ref = NULL;
    const char *reads_path = NULL;
    int threads = get_nprocs();
    int batch   = DEFAULT_BATCH;

    /* Flag parsing; fall back to positional if first arg is not a flag */
    if (argc > 1 && argv[1][0] == '-') {
        for (int i = 1; i < argc; ++i) {
            if (!strcmp(argv[i], "-r") || !strcmp(argv[i], "--ref")) {
                if (++i >= argc) { usage(argv[0]); return 1; }
                ref = argv[i];
            } else if (!strcmp(argv[i], "-i") || !strcmp(argv[i], "--input")) {
                if (++i >= argc) { usage(argv[0]); return 1; }
                reads_path = argv[i];
            } else if (!strcmp(argv[i], "-t") || !strcmp(argv[i], "--threads")) {
                if (++i >= argc) { usage(argv[0]); return 1; }
                threads = atoi(argv[i]);
            } else if (!strcmp(argv[i], "-B") || !strcmp(argv[i], "--batch")) {
                if (++i >= argc) { usage(argv[0]); return 1; }
                batch = atoi(argv[i]);
            } else if (!strcmp(argv[i], "-b") || !strcmp(argv[i], "--band")) {
                if (++i >= argc) { usage(argv[0]); return 1; }
                g_sw_band = atoi(argv[i]);
            } else if (!strcmp(argv[i], "-h") || !strcmp(argv[i], "--help")) {
                usage(argv[0]);
                return 0;
            } else {
                fprintf(stderr, "Unknown argument: %s\n", argv[i]);
                usage(argv[0]);
                return 1;
            }
        }
    } else if (argc >= 3) {
        ref = argv[1];
        reads_path = argv[2];
        if (argc > 3) threads = atoi(argv[3]);
        if (argc > 4) batch   = atoi(argv[4]);
        if (argc > 5) g_sw_band = atoi(argv[5]);
    }

    if (!ref || !reads_path) {
        usage(argv[0]);
        return 1;
    }

    if (g_sw_band < 0) g_sw_band = 0;
    if (threads <= 0) threads = get_nprocs();
    if (batch <= 0)   batch = DEFAULT_BATCH;

    FILE *fp = strcmp(reads_path, "-") ? fopen(reads_path, "r") : stdin;
    if (!fp) { perror("fopen"); return 1; }

    setvbuf(stdout, NULL, _IOFBF, 1 << 20);

    pthread_t *th = calloc(threads, sizeof(*th));
    worker_arg_t *wa = calloc(threads, sizeof(*wa));

    for (int i = 0; i < threads; ++i) {
        wa[i].tid = i;
        wa[i].ref = ref;
        wa[i].ref_len = strlen(ref);
        pthread_create(&th[i], NULL, worker_main, &wa[i]);
    }

    produce(fp, batch);
    if (fp != stdin) fclose(fp);

    for (int i = 0; i < threads; ++i)
        pthread_join(th[i], NULL);

    free(th);
    free(wa);
    return 0;
}
