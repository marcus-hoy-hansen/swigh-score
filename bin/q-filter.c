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
	char buff[len], currentchar, qual[len], dna[len], id[len];
	char fastqline[4][len];
	int lines = 0;
	fastqfile = fopen(argv[1], "r");
	double score = 0.00;
	int mean;
	
	while(!feof(fastqfile)) {
		currentchar = fgetc(fastqfile);
		
		if(currentchar == '\n') lines++;
	
	}	
	rewind(fastqfile);
	for (int i = 0; i < lines/4; i++) {

		for (int j=1; j <= 4; ++j) {
			fgets(buff, len, fastqfile);
                	strcpy(fastqline[j], buff);
		}
		
		score = 0;
		for (int u = 0; u < strlen(buff); u++) score += (buff[u]-33);
	
		mean = (score/strlen(buff));
		if(mean>=lowerqual && strlen(fastqline[2])>=lowerlength) {
			printf("%s%s+\n%s", fastqline[1], fastqline[2], fastqline[4]);
		}
	}
	fclose(fastqfile);
	return 0;
}
