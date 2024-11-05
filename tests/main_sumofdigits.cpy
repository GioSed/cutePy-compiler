def main_sumofdigits():
#{
	#declare x, sum
	x = int(input());
	sum = 0;
	while (x > 0):
	#{
		sum = sum + (x % 10);
		x = x // 10;
	#}
	print(sum);
#}
if __name__ == ”__main__”:
	#$ call of main functions #$
	main_sumofdigits();