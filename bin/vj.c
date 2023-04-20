#include<stdio.h>
#include<string.h>

 

float SW(char* arg1, char* arg2) {

	int match = 0;
	double val = 0.000;
	int cnum1 = strlen(arg1);
	char str1[cnum1];
	int cnum2 = strlen(arg2);
	char str2[cnum2];
	double SWpercent;

	strcpy(str1,arg1);
	strcpy(str2,arg2);
	
	int arr[cnum2][cnum1];

	for(int i=0;i<cnum2;i++){
		for(int j=0;j<cnum1;j++){
			if(str1[j]==str2[i])
				arr[i][j]=1;
			else
				arr[i][j]=0;
		}
	}

	int c;
	int ul;
	int l;
	int u;

	for(int i=1;i<cnum2;i++){
		for(int j=1;j<cnum1;j++){
			
			c=arr[i][j];
			ul=arr[i-1][j-1];
			l=arr[i][j-1];
			u=arr[i-1][j];
			

			if( c>0 && (ul+1)>(l-1) && (ul+1)>(u-1)) {
				arr[i][j] = ul+1;
			
			} else if( c==0 && (ul+1)>(l-1) && (ul+1)>(u-1)) {
				arr[i][j] = ul-1;

			} else if((l-1)>(u-1)) {
				arr[i][j] = l-1;

			} else if((u-1)>(l-1)) {
				arr[i][j] = u-1;
			} else { 
				arr[i][j] = 0;
			}
		
			
			if(arr[i][j]<0) arr[i][j] = 0;
			
			if(arr[i][j]>val) val = arr[i][j];
				
		}
	}

	if(cnum1 < cnum2) 
		SWpercent = val/(double)cnum1;
	else
		SWpercent = val/(double)cnum2;

	//printf("%s\t", str1);
	//printf("%f", SWpercent);
	return SWpercent;
}

int main(int argc,char* argv[]) {
        
	FILE *fp,*fp2;
	int len = 100000;
	char ch, ch2,buff[len],dna[len],dna2[len],sw[len],sw2[len];
	int lines = 0;
	int lines2 = 0;
	fp = fopen(argv[2], "r");
	fp2 = fopen(argv[1], "r");
	int i = 0;
	int i2 =0;
	float f=0.0000;
	float score=0.0000;
	while(!feof(fp)) {
		ch = fgetc(fp);
		if(ch == '\n') {
			lines++;
		}
	}

	while(!feof(fp2)) {
                ch2 = fgetc(fp2);
                if(ch2 == '\n') {
			//printf("%s\n", "line");
                        lines2++;
                }
        }
	
	rewind(fp);
	rewind(fp2);
	while (i2 <= lines2) {
		i2++;
		fgets(buff, len, fp2);
		strcpy(dna2, buff);
		while (i <= lines) {
			i++;
			fgets(buff, len, fp);
			strcpy(dna, buff);
			f=SW(dna2,dna);
			if(f>score) {
				score=f;
				strncpy(sw, dna, strlen(dna)-1);
				strncpy(sw2, dna2, strlen(dna2)-1);
			}
		}
		if(score<0.9999) {
			printf("%f\t%s\t%s\n", score, sw, sw2);
		}
		rewind(fp);
		score=0.0000;
		i=0;
	}
	//printf("%s", "\n");
        return 0;
}
