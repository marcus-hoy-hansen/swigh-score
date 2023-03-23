#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>

int main(int argc,char* argv[]) {

  int lowerlength = 200;
	int lowerqual = 20;
	if(argc>1) {
		lowerqual=atoi(argv[2]);
	}

	if (argc>2) {
		lowerlength=atoi(argv[3]);
	}


	FILE *fp;
	int len = 100000;
	char buff[len], ch, qual[len], dna[len], plus[len], id[len];
	int lines = 0;
	fp = fopen(argv[1], "r");
	int i = 0;
	int u;
	double score = 0.00;
	int mean;
	
	while(!feof(fp)) {
		ch = fgetc(fp);
		if(ch == '\n') {
			lines++;
		}
	}
	
	printf("%i",lines);
	rewind(fp);
	
	while (i <= lines/4) {
		i++;
		fgets(buff, len, fp);
		strcpy(id, buff);
		fgets(buff, len, fp);
		strcpy(dna, buff);
		fgets(buff, len, fp);
		strcpy(plus, buff);
		fgets(buff, len, fp);
		strcpy(qual, buff);
		score = 0;
		for (u = 0; u < strlen(buff); u++) {
			score = score + (buff[u]-33);
		}
	
		mean = (score/strlen(buff));
		if(mean>=lowerqual && strlen(dna)>lowerlength) {
			printf("%s", id);
			printf("%s", dna);
			printf("%s", plus);
			printf("%s", qual);
		}
	}
	fclose(fp);
	return 0;
}
