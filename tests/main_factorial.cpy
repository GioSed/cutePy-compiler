def main_factorial():
#{
	#declare n,fact
	n = int(input());
	fact = 1;
	while (n > 0):
	#{
		fact = fact * n;
		n = n - 1;
	#}
	print(fact);
#}
if __name__ == ”__main__”:
	#$ call of main functions #$
	main_factorial();