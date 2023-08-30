#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>

int main(int argc,char* argv[]) {

  	int lowerlength = 200;
	double lowerqual = 20.0;
	int runmode=1;
	if(argc>2) lowerqual=atof(argv[2]);
	if (argc>3) lowerlength=atoi(argv[3]);
	if (argc>4) runmode=2;

	double P=pow(10,-lowerqual/10);
	FILE *fastqfile;
	int len = 10000;
	char buff[len], currentchar;
	char fastqline[4][len];
	int lines = 0;
	fastqfile = fopen(argv[1], "r");
	double score = 0.000000;
	double mean;
	
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
		if(runmode==1) {
			for (int u = 0; u < strlen(buff)-1; u++) score += (buff[u]-33);
			mean = -1*(score/strlen(buff))/10;
			mean = pow(10,mean);

		} else {
			for (int u = 0; u < strlen(buff)-1; u++) {
				score = score+pow(10,-1*(double)(buff[u]-33)/10);
			}	
			
			mean = (score/(double)strlen(buff));
		}
		if(mean<=P && strlen(fastqline[2])>=lowerlength) {
			printf("%s%s+\n%s", fastqline[1], fastqline[2], fastqline[4]);
		}
	}
	fclose(fastqfile);
	return 0;
}
