#include<stdio.h>
#include<string.h>

// gcc SWscore.c -o SWscore
 
int main(int argc,char* argv[])
{
	int match = 1;
	int val = 0;

	int cnum1 = strlen(argv[1]);
	char str1[cnum1+10];
	int cnum2 = strlen(argv[2]);
	char str2[cnum2+10];
	double SWpercent;

	strcpy(str1,argv[1]);
	strcpy(str2,argv[2]);
	
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
	int maxc;
	int maxr;

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
			
			if(arr[i][j]>val) {
				val = arr[i][j];
				maxr = i;
				maxc = j;
			}	
		}
	}
	int crow = maxr;
	int ccol = maxc;

	char alignment1[cnum1];
	char alignment2[cnum2];
	char alignmentmatch[1000];
	int alignpos = 0;	

	for(int i=val;i>0;i--){
		
		if(str1[ccol]==str2[crow]) {
                        match=match+1;
                        alignmentmatch[alignpos] = '|';
                        alignment1[alignpos] = str1[ccol];
                        alignment2[alignpos] = str2[crow];
                        alignpos = alignpos+1;
                }
	
		ul=arr[crow-1][ccol-1];
		l=arr[crow][ccol-1];
		u=arr[crow-1][ccol];
		
		if(ul>=l && ul>=u) {
			crow = crow - 1;
			ccol = ccol - 1;
		} else if(l>u) {
			ccol = ccol - 1;
		} else {
			crow = crow - 1;
		}
		
		i = arr[crow][ccol];
	}
	alignmentmatch[alignpos + 1] = '\0';
	alignment1[alignpos + 1] = '\0';
	alignment2[alignpos + 1] = '\0';

	SWpercent = (double)val/(double)match;

	printf("%s\t", str1);
	printf("%f\t", SWpercent);
	printf("%i\t", val);
	printf("%i\t", match);
	printf("%f\n", SWpercent*((double)val+(double)match));
	return 0;
}
