
#include<stdio.h>
#include<string.h>

// gcc SWscore.c -o SWscore
 
int main(int argc,char* argv[])
{
	int match = 0;
	double val = 0.000;
	int cnum1 = strlen(argv[1]);
	char str1[cnum1];
	int cnum2 = strlen(argv[2]);
	char str2[cnum2];
	double SWpercent;

	strcpy(str1,argv[1]);
	strcpy(str2,argv[2]);
	
	int arr[cnum2][cnum1];

	for(int i=0;i<cnum2;i++){
		for(int j=0;j<cnum1;j++){
			if(str1[j]==str2[i])
				arr[i][j]=1;//printf("1\t");
			else
				arr[i][j]=0;//printf("0\t");
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

	printf("%s\t", str1);
	printf("%f\n", SWpercent);

	return 0;
}
