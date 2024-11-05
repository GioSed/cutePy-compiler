def main_fibonacci():
#{
	#declare n, a, b, i
	n = int(input());
	a = 0;
	b = 1;
	i = 2;
	print(a);
	print(b);
	while (i < n):
	#{
		c = a + b;
		print(c);
		a = b;
		b = c;
		i = i + 1;
	#}
#}
if __name__ == ”__main__”:
	#$ call of main functions #$
	main_fibonacci();