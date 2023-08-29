#include <stdio.h>
#include <string.h>
#include <stdlib.h>

int main(int argc,char* argv[]) {

  	int lowerlength = 200;
	int lowerqual = 20;
	
	if(argc>1) lowerqual=atoi(argv[2]);

	if (argc>2) lowerlength=atoi(argv[3]);

	FILE *fastqfile;
	int len = 10000;
	char buff[len], currentchar, qual[len], dna[len], plus[len], id[len];
	int lines = 0;
	fastqfile = fopen(argv[1], "r");
	int i = 0;
	int u;
	double score = 0.00;
	int mean;
	
	while(!feof(fastqfile)) {
		currentchar = fgetc(fastqfile);
		
		if(currentchar == '\n') lines++;
	
	}	
	rewind(fastqfile);
	
	while (i <= lines/4) {
		i++;
		fgets(buff, len, fastqfile);
		strcpy(id, buff);
		fgets(buff, len, fastqfile);
		strcpy(dna, buff);
		fgets(buff, len, fastqfile);
		fgets(buff, len, fastqfile);
		strcpy(qual, buff);
		score = 0;
		for (u = 0; u < strlen(buff); u++) {
			score += (buff[u]-33);
		}
	
		mean = (score/strlen(buff));
		if(mean>=lowerqual && strlen(dna)>=lowerlength) {
			printf("%s%s+\n%s", id, dna, qual);
		}
	}
	fclose(fastqfile);
	return 0;
}
