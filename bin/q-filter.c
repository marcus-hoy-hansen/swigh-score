#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>

int main(int argc,char* argv[]) {

	int lowerlength = 200;
	double lowerqual = 20.0;
	int runmode=1;

	// Parse command-line arguments
	if (argc > 2) lowerqual = atof(argv[2]);
	if (argc>3) lowerlength=atoi(argv[3]);
	if (argc>4) runmode=2;

	int lines = 0;
	int len = 10000;
	double P=pow(10,-lowerqual/10);
	double score = 0.0;
	double mean;
	char buff[len], bufflen, currentchar,fastqline[4][len];

	// 1. Open the FASTQ file and count lines
	FILE *fastqfile;
	fastqfile = fopen(argv[1], "r");
	while(!feof(fastqfile)) {
		currentchar = fgetc(fastqfile);
		if(currentchar == '\n') lines++;
	}
	rewind(fastqfile);
	
	// 2. Process the FASTQ entries
	for (int i = 0; i < lines/4; i++) {
		for (int j=1; j <= 4; ++j) {
			fgets(buff, len, fastqfile);
                	strcpy(fastqline[j], buff);
		}
		
		score = 0;
		bufflen = strlen(buff)-1;

		// 3. Calculate score and mean based on runmode
		if(runmode==2) {
			for (int u = 0; u < bufflen; u++) {
				score = score+pow(10,-1*(double)(buff[u]-33)/10);
			}	
			mean = (score/(double)bufflen);

		} else {
			for (int u = 0; u < bufflen; u++) score += (buff[u]-33);
			mean = -1*(score/bufflen)/10;
			mean = pow(10,mean);
		}
		
		// 4. Check conditions and print if satisfied
		if(mean<=P && strlen(fastqline[2])>=lowerlength) {
			printf("%s%s+\n%s", fastqline[1], fastqline[2], fastqline[4]);
		}
	}

	// Close the FASTQ file
	fclose(fastqfile);

	return 0;
}
