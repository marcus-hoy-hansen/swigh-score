#include <stdio.h>
#include <string.h>

int main(int argc, char *argv[]) {
	// Declare variables
	int match = 1;
	int val = 0;
	int len1 = strlen(argv[1]);
	int len2 = strlen(argv[2]);
	char str1[len1 + 10], str2[len2 + 10];
	strcpy(str1, argv[1]);
	strcpy(str2, argv[2]);
	double SWpercent, swighscore;
	
	// 1. Create and initialize the scoring matrix
	int scoreMatrix[len2][len1];
	for (int i = 0; i < len2; i++) {
		for (int j = 0; j < len1; j++) {
			scoreMatrix[i][j] = (str1[j] == str2[i]) ? 1 : 0;
		}
	}

	// 2. Initialize variables for traceback
	int currentCell, upperLeft, left, up;
	int maxRow, maxCol;

	// Perform Smith-Waterman algorithm
	for (int i = 1; i < len2; i++) {
		for (int j = 1; j < len1; j++) {
			currentCell = scoreMatrix[i][j];
			upperLeft = scoreMatrix[i - 1][j - 1];
			left = scoreMatrix[i][j - 1];
			up = scoreMatrix[i - 1][j];

			// Update current cell based on traceback rules
			scoreMatrix[i][j] = (currentCell > 0 
				&& (upperLeft + 1 > left - 1) 
				&& (upperLeft + 1 > up - 1))
			? upperLeft + 1
			: ((currentCell == 0 
				&& (upperLeft + 1 > left - 1) 
				&& (upperLeft + 1 > up - 1))
			? upperLeft - 1
			: ((left - 1 > up - 1)? left - 1
			: ((up - 1 > left - 1)? up - 1: 0)));

			// Update max value and position
			if (scoreMatrix[i][j] > val) {
				val = scoreMatrix[i][j];
				maxRow = i;
				maxCol = j;
			}
		}
	}

	// Initialize traceback variables
	int currentRow = maxRow;
	int currentCol = maxCol;

	// 3. Perform traceback
	for (int i = val; i > 0; i--) {
		if (str1[currentCol] == str2[currentRow]) match++;

		upperLeft = scoreMatrix[currentRow - 1][currentCol - 1];
		left = scoreMatrix[currentRow][currentCol - 1];
		up = scoreMatrix[currentRow - 1][currentCol];

		// Update current position based on traceback rules
		if (upperLeft >= left && upperLeft >= up) {
			currentRow--;
			currentCol--;
		} else if (left > up) {
			currentCol--;
		} else {
			currentRow--;
		}

		i = scoreMatrix[currentRow][currentCol];
	}

	// 4. Calculate SWpercent and print out results
	SWpercent = (double)val / (double)match;
	swighscore = SWpercent * ((double)val + (double)match);

	printf("%s\t%f\t%i\t%i\t%f\n", str1, SWpercent, val, match, swighscore);
	return 0;
}
