import sys
import os

## GLOBAL DECLERATIONS ##

#------- CONSTANTS -------#
MEM_BLOCK_SIZE = 4 # For symbols table
#-------------------------#

temporary_states = {0,1,2,3,4,5,6,7,8,9,10}
final = 99
line = 1
skip_char = 0 

next_label = 1
quad_list = []
next_temp_num = 1

cond_jump_code_dict = {
	'==': 'beq',
	'!=': 'bne',
	'<': 'blt',
	'>': 'bgt',
	'<=': 'ble',
	'>=': 'bge',
}

operations_code_dict = {
	'+': 'add',
	'-': 'sub',
	'*': 'mul',
	'//': 'div'
}

tokens_dict = {
    '+' : 'TOKEN_plus',
    '-' : 'TOKEN_minus',
    '*' : 'TOKEN_times',
    '//' : 'TOKEN_divide',
    '<' : 'TOKEN_less',
    '>' : 'TOKEN_greater',
    '=' : 'TOKEN_assignment',
    '==': 'TOKEN_equal',
    '!=': 'TOKEN_nonEqual',
    '<=' : 'TOKEN_lessEqual',
    '>=' : 'TOKEN_greaterEqual',
    '(' : 'TOKEN_leftParenthesis',
    ')' : 'TOKEN_rightParenthesis',
    '[' : 'TOKEN_leftBracket',
    ']' : 'TOKEN_rightBracket',
    '{' : 'TOKEN_leftBrace',
    '}' : 'TOKEN_rightBrace',
    ';' : 'TOKEN_semiColon',
    ':' : 'TOKEN_colon',
    ',' : 'TOKEN_comma',
    '.' : 'TOKEN_programm_end',
    'declare' : 'TOKEN_declare',
    'def' : 'TOKEN_def',
    'if' : 'TOKEN_if',
    'else' : 'TOKEN_else',
    'while' : 'TOKEN_while',
    'default' : 'TOKEN_default',
    'not' : 'TOKEN_not',
    'and' : 'TOKEN_and',
    'or' : 'TOKEN_or',
    'return' : 'TOKEN_return',
    'input' : 'TOKEN_input',
    'print' : 'TOKEN_print',
    'EOF' : 'TOKEN_eof',
    'ID' : 'TOKEN_id',
    "number" : 'TOKEN_number',
    '.' : 'TOKEN_dot',
    '#$' : 'TOKEN_comment',
    '#{' : 'TOKEN_left_hashbracket',
    '#}' : 'TOKEN_right_hashbracket',
    '#' : 'TOKEN_hashtag'
}

class Token:
    def __init__(self, family, value, line):
        self.family = family
        self.value = value
        self.line = line

    def get_token_type(self):
        return self.token_type


def create_token(word, line):
	global token
	if word in tokens_dict.keys():
		token = Token(tokens_dict[word], word, line)
	elif word.isdigit():
		token = Token(tokens_dict['number'], word, line)
	else:
		token = Token(tokens_dict['ID'], word, line)

#------- INT CODE FUNCTIONS -------#

class Quad():
	def __init__(self, q_id, op, x, y, z):
		self.q_id = q_id
		self.op = op
		self.x = x
		self.y = y
		self.z = z

	def __str__(self):
		return f"{self.q_id}: {self.op}, {self.x}, {self.y}, {self.z}"

	def get_q_id(self): return self.q_id
	def get_op(self): return self.op
	def get_x(self): return self.x
	def get_y(self): return self.y
	def get_z(self): return self.z


def gen_quad(op, x, y, z):
	global next_label

	quad_list.append(Quad(next_label, op, x, y, z))
	next_label += 1

def next_quad(): #returns the id of the next quad
	global next_label
	return next_label

def new_temp():
	global next_temp_num

	t_new = "T%" + str(next_temp_num)
	next_temp_num += 1

	add_temp_var(t_new) # Add temporary variable in symbols table
	
	return t_new

def empty_list():
	return []

def make_list(label):
	return [label]

def merge_list(list1, list2): #Returns a merge of the two lists
	return list1 + list2

def backpatch(lst, z): #fills the last element of quads with z
	for q in quad_list:
		if q.q_id in lst:
			q.z = z

#----------------------------------#

#------------ SYMBOLS TALBE ------------#

class Table:
	def __init__(self):
		self.scope_list = []

	def __str__(self):
		t_str = "SYMBOLS TABLE:\n"

		for s in self.scope_list[::-1]:
			t_str += f"({s.get_level()})"
			for e in s.entity_list:
				t_str += "<--|" + e.name

				if isinstance(e, Variable): t_str += f"/{e.offset}"
				if isinstance(e, Parameter): t_str += f"/{e.offset}/{e.mode}"
				if isinstance(e, (Function, Procedure)): t_str += f"/{e.framelength}/{e.starting_quad}" if e.framelength > 0 else ""

				t_str += '|'

			t_str += "\n"

			if s != self.scope_list[0]:
				t_str += ' ^\n |\n'

		return t_str


	def add_entity(self, e):
		self.scope_list[-1].add_entity(e)

	def add_scope(self):
		self.scope_list.append(Scope(len(self.scope_list)))

	def remove_scope(self):
		del self.scope_list[-1]

	def update_fields(self,
					  starting_quad,
					  framelength):
		self.scope_list[-2].update_last_entity(starting_quad,
											   framelength)


	def add_formal_parameter(self, f_param):
		self.scope_list[-2].add_f_param_to_last_entity(f_param)


	def search_record(self, name):
		# Search scopes in reverse order
		for s in self.scope_list[::-1]:
			for e in s.get_entity_list():
				if e.name == name: return (e, s.get_level())

		return None

	def get_cur_scope_var_num(self):
		return self.scope_list[-1].count_variables()

	def get_current_scope_level(self):
		return len(self.scope_list) - 1 # Scopes are numbered 0..(n-1)


class Scope:
	def __init__(self, level):
		self.level = level
		self.entity_list = []

	def get_level(self): return self.level

	def get_entity_list(self): return self.entity_list

	def count_variables(self):
		count = len([e for e in self.entity_list if isinstance(e, (Variable,
																   TemporaryVariable,
																   Parameter))])
		
		return count

	def add_entity(self, e):
		self.entity_list.append(e)

	def update_last_entity(self,
						   starting_quad,
						   framelength):
		self.entity_list[-1].set_starting_quad(starting_quad)
		self.entity_list[-1].set_framelength(framelength)

	def add_f_param_to_last_entity(self,
								   f_param):
		self.entity_list[-1].add_formal_param(f_param)



class Entity:
	def __init__(self, name):
		self.name = name


class Variable(Entity):
	def __init__(self, name, datatype, offset):
		super().__init__(name)
		self.datatype = datatype # Only one datatype in our case, int
		self.offset = offset

	def get_offset(self): return self.offset


class TemporaryVariable(Variable):
	def __init__(self, name, datatype, offset):
		super().__init__(name,
						 datatype,
						 offset)


class Procedure(Entity):
	def __init__(self, name, starting_quad, framelength, formal_parameters):
		super().__init__(name)
		self.starting_quad = starting_quad
		self.framelength = framelength
		self.formal_parameters = formal_parameters # list

	def set_starting_quad(self, starting_quad): self.starting_quad = starting_quad

	def set_framelength(self, framelength): self.framelength = framelength

	def add_formal_param(self, f_param): self.formal_parameters.append(f_param)

	def get_framelength(self): return self.framelength

	def get_starting_quad(self): return self.starting_quad


class Function(Procedure):
	def __init__(self, name, datatype, starting_quad, framelength, formal_parameters):
		super().__init__(name,
						 starting_quad,
						 framelength,
						 formal_parameters)
		self.datatype = datatype


class FormalParameter(Entity):
	def __init__(self, name, datatype, mode):
		super().__init__(name)
		self.datatype = datatype
		self.mode = mode # Only one mode in our case, 'in' (by value)


class Parameter(FormalParameter):
	def __init__(self, name, datatype, mode, offset):
		super().__init__(name, datatype, mode)
		self.offset = offset

	def get_offset(self): return self.offset


#--- Helper functions ---#
def add_var(name, datatype='int'): # We set datatype='int' since we allow only integer in our case
	global symbols_table
	symbols_table.add_entity(Variable(name=name,
									  datatype=datatype,
									  offset=3*MEM_BLOCK_SIZE + MEM_BLOCK_SIZE*symbols_table.get_cur_scope_var_num()))


def add_temp_var(name, datatype="int"): # We set datatype='int' since we allow only integer in our case
	global symbols_table
	symbols_table.add_entity(TemporaryVariable(name=name,
									  		   datatype=datatype,
									  		   offset=3*MEM_BLOCK_SIZE + MEM_BLOCK_SIZE*symbols_table.get_cur_scope_var_num()))

def add_parameter(name, datatype='int', mode='cv'):
	global symbols_table
	symbols_table.add_entity(Parameter(name=name,
							  		   datatype=datatype,
							  		   mode=mode,
							  		   offset=3*MEM_BLOCK_SIZE + MEM_BLOCK_SIZE*symbols_table.get_cur_scope_var_num()))

def add_formal_parameter(name, datatype='int', mode='cv'):
	global symbols_table
	symbols_table.add_formal_parameter(FormalParameter(name=name,
										  		       datatype=datatype,
										  		       mode=mode))

def add_function(name, datatype='int'):
	global symbols_table
	symbols_table.add_entity(Function(name=name,
									  datatype=datatype,
									  starting_quad=-1,
									  framelength=-1,
									  formal_parameters=[]))

def add_procedure(name):
	global symbols_table
	symbols_table.add_entity(Procedure(name=name,
									   starting_quad=-1,
									   framelength=-1,
									   formal_parameters=[]))


# Symbols table definition
symbols_table = Table()

#---------------------------------------#

def open_cpy_file():
	global file, filename

	filename = os.path.split(sys.argv[1])[1]

	if len(sys.argv) < 2:
		print("Error: There is no input file")
		sys.exit()
	if filename[-3:] != "cpy":
		print("Error: Input file is not a CutePy file")
		sys.exit()
		
	file = open(filename, "r", encoding="utf8") # TODO: encoding="utf8" was added, check if needed


def error(line, missing_token):
    print(f"Error: line {line} - {missing_token} is missing")
    exit()

def show_custom_error(msg, line):
	print(f"Error: Line {line}\n\t{msg}")
	exit()

def parser():
	global token
	lex()
	start_rule()

#--------------- LEX ---------------#

def lex():
	global line
	global skip_char

	word = []
	state_cur = 0
	move_file_pointer = False

	while state_cur in temporary_states:
		previous_pos = file.tell()
		char = file.read(1)
		word.append(char)

		if state_cur == 0:
			if char == "":
				create_token("EOF",line)
				break
			elif char.isspace():
				state_cur = 0
			elif char.isalpha() or char == "_":
				state_cur = 1
			elif char.isdigit():
				state_cur = 2
			elif char == '<':
				state_cur = 3
			elif char == '>':
				state_cur = 4
			elif char == '#':
				state_cur = 5
			elif char in ('+', '-', '*', ',', ';', ':', '{', '}', '(', ')', '[', ']'):
				state_cur = final #temp value
			elif char == '!':
				state_cur = 6
			elif char == '/':
				state_cur = 9
			elif char == '=':
				state_cur = 10
			elif char != '"' and char != "”":
				show_custom_error(f"{char} is not recognized.", token.line)
		elif state_cur == 1:
			if not char.isalnum() and char != "_" and char != '"' and char != "”":
				state_cur = final
				move_file_pointer = True

			# Check length is max 30 characters
			if len([c for c in word if not c.isspace()]) > 30:
				show_custom_error("identifiers should not be more than 30 characters long.", line)
		elif state_cur == 2:
			if not char.isdigit():
				state_cur = final
				move_file_pointer = True

			# Check number is in valid range
			num = int(''.join([c for c in word if c.isdigit()]))
			if num < -(2**32 - 1) or num > 2**32 - 1:
				show_custom_error("only integers in interval [-(2^32 - 1), 2^32 - 1] are allowed.", line)
		elif state_cur == 3:
			if char != '=':
				move_file_pointer = True
			state_cur = final
		elif state_cur == 4:
			if char != "=":
				move_file_pointer = True
			state_cur = final
		elif state_cur == 5:
			if char not in ('{','}','$'):
				move_file_pointer = True
			state_cur = final
			if char == '$':
				state_cur = 7
		elif state_cur == 6:
			if char != "=":
				move_file_pointer = True
			state_cur = final
		elif state_cur == 7:
			if char == "#":
				state_cur = 8
			elif char == "":
				show_custom_error("EOF reached while closing comment '#$' was expected.", line)
		elif state_cur == 8:
			if char == "$":
				state_cur = 0
				del word[:]
			elif char != "":
				state_cur = 7
			else:
				show_custom_error("EOF reached while closing comment '#$' was expected.", line)
		elif state_cur == 9:
			if char != "/":
				move_file_pointer = True
			state_cur = final
		elif state_cur == 10:
			if char != "=":
				move_file_pointer = True
			state_cur = final
		
		if char.isspace():
			del word[-1]
			move_file_pointer = False
			if char == "\n":
				line += 1

	if move_file_pointer == True:
		del word[-1]
		file.seek(previous_pos)

	if state_cur == final:
		word = ''.join(word)
		create_token(word, line)

#-----------------------------------#


#-------------- SYNTACTIC ANALYZER -------------------#

def start_rule():
	symbols_table.add_scope() # Create new scope
	def_main_part()
	gen_quad('begin_block', filename.split('.')[0], '_', '_')
	call_main_part()
	gen_quad('halt', '_', '_', '_')
	gen_quad('end_block', filename.split('.')[0], '_', '_')

	generate_final_code()


def def_main_part():
	while( token.family == "TOKEN_def"):
		def_main_function()
	

def def_main_function():
	global symbols_table

	if token.family == "TOKEN_def":
		lex()
		cur_func_name = token.value
		if token.family == "TOKEN_id":

			add_procedure(cur_func_name)
			symbols_table.add_scope() # Create new scope

			lex()
			if token.family == "TOKEN_leftParenthesis":
				lex()
				if token.family == "TOKEN_rightParenthesis":
					lex()
					if token.family == "TOKEN_colon":
						lex()
						if token.family == "TOKEN_left_hashbracket":
							lex()
							declarations()
							def_function()

							starting_quad = next_quad()
							gen_quad('begin_block', cur_func_name, '_', '_')

							statements()
							gen_quad('end_block', cur_func_name, '_', '_')
							if token.family == "TOKEN_right_hashbracket":
								var_num = symbols_table.get_cur_scope_var_num()
								symbols_table.update_fields(starting_quad, 3*MEM_BLOCK_SIZE + MEM_BLOCK_SIZE*var_num)
								print(symbols_table)


								generate_final_code()
								symbols_table.remove_scope() # Remove current scope

								lex()
							else:
								error(token.line, "#}")
						else:
							error(token.line, "#{")
					else:
						error(token.line, ":")
				else:
					error(token.line, ")")
			else:
				error(token.line, "(")
		else:
			error(token.line, "id")
	else:
		error(token.line, "def")


def declarations():
	declaration_line()

def declaration_line():
	# if token.family == "TOKEN_id":
	# 	lex()
	# 	id_list()
	while(token.family == "TOKEN_hashtag"):
		lex()
		if token.family == "TOKEN_declare":
			id_list()
		else:
			error(token.line, "declare")

def id_list():
	# Store who called the function for symbols table
	origin = token.family

	lex()
	if token.family == "TOKEN_id":
		if origin == "TOKEN_declare":
			add_var(name=token.value)
		else:
			add_parameter(name=token.value)
			add_formal_parameter(name=token.value)

		lex()
		while(token.family == "TOKEN_comma"):
			lex() # Consume ID
			if token.family == "TOKEN_id":
				if origin == "TOKEN_declare":
					add_var(name=token.value)
				else:
					add_parameter(name=token.value)
					add_formal_parameter(name=token.value)
			else:
				show_custom_error("ID was expected.", token.line)

			lex()

def def_function():
	global symbols_table

	while(token.family == "TOKEN_def"):
		lex()
		if token.family == "TOKEN_id":
			cur_func_name = token.value

			add_function(cur_func_name)
			symbols_table.add_scope() # Create new scope

			lex()
			if token.family == "TOKEN_leftParenthesis":
				id_list()
				if token.family == "TOKEN_rightParenthesis":
					lex()
					if token.family == "TOKEN_colon":
						lex()
						if token.family == "TOKEN_left_hashbracket":
							lex()
							declarations()
							def_function()

							starting_quad = next_quad()
							gen_quad('begin_block', cur_func_name, '_', '_')

							statements()
							gen_quad('end_block', cur_func_name, '_', '_')
							if token.family == "TOKEN_right_hashbracket":
								var_num = symbols_table.get_cur_scope_var_num()
								symbols_table.update_fields(starting_quad, 3*MEM_BLOCK_SIZE + MEM_BLOCK_SIZE*var_num)
								
								print(symbols_table)
								
								generate_final_code()
								symbols_table.remove_scope() # Remove current scope


								lex()
							else:
								error(token.line,"#}")
						else:
							error(token.line,"#{")
					else:
						error(token.line,":")
				else:
					error(token.line,")")
			else:
				error(token.line,"(")
		else:
			error(token.line,"id")


def statements():
	while(token.family in ('TOKEN_id', 'TOKEN_print', 'TOKEN_return', 'TOKEN_if', 'TOKEN_while')):
		statement()

def statement():
	if token.family in ('TOKEN_id', 'TOKEN_print', 'TOKEN_return'):
		simple_statement()
	elif token.family in ("TOKEN_if", "TOKEN_while"):
		structured_statement()

def simple_statement():
	global symbols_table
	if token.family == 'TOKEN_id':

		if symbols_table.search_record(token.value) == None:
			show_custom_error(f"'{token.value}' is not declared.", token.line)

		assignment_stat(token.value)
	elif token.family == 'TOKEN_print':
		print_stat()
	elif token.family == 'TOKEN_return':
		return_stat()

def structured_statement():
	if token.family == 'TOKEN_if':
		if_stat()
	elif token.family == 'TOKEN_while':
		while_stat()

def assignment_stat(id_name):
	lex()
	if token.family == "TOKEN_assignment":
		lex()
		if token.value == "int":
			lex()
			if token.family == "TOKEN_leftParenthesis":
				lex()
				if token.family == "TOKEN_input":
					gen_quad('in', id_name, '_', '_')
					lex()
					if token.family == "TOKEN_leftParenthesis":
						lex()
						if token.family == "TOKEN_rightParenthesis":
							lex()
							if token.family == "TOKEN_rightParenthesis":
								lex()
								if token.family == "TOKEN_semiColon":
									lex()
								else:
									error(token.line,";")
							else:
								error(token.line,")")
						else:
							error(token.line,")")
					else:
						error(token.line,"(")
				else:
					error(token.line,"iput")
			else:
				error(token.line,"(")
		else:
			e_place = expression()

			# Generate assignment quad
			gen_quad("=", e_place, "_", id_name)

			if token.family == "TOKEN_semiColon":
				lex()
			else:
				error(token.line,";")
	else:
		show_custom_error("'=' was expected.", token.line)

def expression():
	sign = optional_sign()
	t1_place = term()

	if sign == '-':
		w = new_temp()
		gen_quad('-', 0, t1_place, w)
		t1_place = w

	while(token.value == "+" or token.value == "-"):
		op_cur = token.value # Keep operation symbol to generate quad

		lex()
		t2_place = term()

		# {p1}
		w = new_temp()
		gen_quad(op_cur, t1_place, t2_place, w)
		t1_place = w

	# {p2}
	e_place = t1_place

	return e_place


def optional_sign():
	sign = None
	if token.value == "+":
		sign = '+'
		lex()
	elif token.value == '-':
		sign = '-'
		lex()

	return sign

def term():
	f1_place = factor()
	while(token.value == "*" or token.value == '//'):
		cur_op = token.value

		lex()
		f2_place = factor()

		# {p1}
		w = new_temp()
		gen_quad(cur_op, f1_place, f2_place, w)
		f1_place = w

	# {p2}
	t_place = f1_place

	return t_place

def factor():
	if token.family == "TOKEN_number":
		f_place = token.value
		lex()
	elif token.family == "TOKEN_leftParenthesis":
		lex()
		f_place = expression()
		if token.family == "TOKEN_rightParenthesis":
			lex()
	elif token.family == "TOKEN_id":
		# {p1}
		f_place = token.value
		lex()

		idtail_res = idtail(f_place) 

		if symbols_table.search_record(f_place) == None:
			show_custom_error(f"'{f_place}' is not declared.", token.line)

		if idtail_res != -1: f_place = idtail_res
	else: # Temporary #1212
		f_place = ""
	
	return f_place

def idtail(id_name):
	if token.family == "TOKEN_leftParenthesis":
		if symbols_table.search_record(id_name) == None:
			show_custom_error(f"function '{id_name}()' is not defined.", token.line)

		lex()
		actual_par_list()
		if token.family == "TOKEN_rightParenthesis":
			w = new_temp()
			gen_quad('par', w, 'ret', '_')
			gen_quad('call', id_name, '_', '_')

			lex()

			return w # Return the temporary variable
		else:
			show_custom_error("')' was expected.", token.line)

	return -1 # Signal that it's not a function

def actual_par_list():
	e_place = expression()

	if e_place == '': return # Temporary #1212

	gen_quad('par', e_place, 'cv', '_')
	while(token.family == "TOKEN_comma"):
		lex()

		e_place = expression()
		gen_quad('par', e_place, 'cv', '_')

def print_stat():
		lex()
		if token.family == "TOKEN_leftParenthesis":
			lex()
			e_place = expression()
			gen_quad('out', e_place, '_', '_')
			if token.family == "TOKEN_rightParenthesis":
				lex()
				if token.family == "TOKEN_semiColon":
					lex()
				else:
					error(token.line,";")
			else:
				error(token.line,")")
		else:
			error(token.line,"(")
	
def return_stat():
		lex()
		if token.family == "TOKEN_leftParenthesis":
			lex()
			e_place = expression()
			gen_quad('ret', e_place, '_', '_')
			
			if token.family == "TOKEN_rightParenthesis":
				lex()
				if token.family == "TOKEN_semiColon":
					lex()
				else:
					error(token.line,";")
			else:
				error(token.line,")")
		else:
			error(token.line,"(")
	

def if_stat():
	lex()
	if token.family == "TOKEN_leftParenthesis":
		lex()
		# {p1}
		B_true, B_false = condition()
		backpatch(B_true, next_quad())

		if token.family == "TOKEN_rightParenthesis":
			lex()
			if token.family == "TOKEN_colon":
				lex()
				if token.family == "TOKEN_left_hashbracket":
					lex()
					statements()

					if token.family == "TOKEN_right_hashbracket":
						lex()	
					else:
						error(token.line,"#}")
				else:
					statement()

				# {p2} Apply false backpatching
				if_list = make_list(next_quad())
				gen_quad('jump', '_', '_', '_')
				backpatch(B_false, next_quad())
			else:
				error(token.line,":")
		else:
			error(token.line,")")

		if token.family =="TOKEN_else":
			lex()
			if token.family =="TOKEN_colon":
				lex()
				if token.family =="TOKEN_left_hashbracket":
					lex()
					statements()

					if token.family == "TOKEN_right_hashbracket":
						lex()
					else:
						error(token.line,"#}")
				else:
					statement()
			else:
				error(token.line,":")
		backpatch(if_list, next_quad())

	else:
		show_custom_error(f"'(' was expected after 'if' keyword.", token.line)


def condition():
	# {p1}
	B_true, B_false = bool_term()
	while(token.value == 'or'):
		# {p2}
		backpatch(B_false, next_quad())
		lex()
		Q2_true, Q2_false = bool_term()

		# {p3}
		B_true, B_false = merge_list(B_true, Q2_true), Q2_false

	return B_true, B_false


def bool_term():
	# {p1}
	Q_true, Q_false = bool_factor()
	while(token.value == 'and'):
		# {p2}
		backpatch(Q_true, next_quad())
		lex()
		R2_true, R2_false = bool_factor()

		# {p3}
		Q_false, Q_true = merge_list(Q_false, R2_false), R2_true

	return Q_true, Q_false

def bool_factor():
	if token.value == "not":
		lex()
		if token.family == 'TOKEN_leftBracket':
			lex()
			B_true, B_false = condition()
			# {p1}
			R_true, R_false = B_false, B_true
			if token.family == 'TOKEN_rightBracket':
				lex()
			else:
				show_custom_error("']' was expected.", token.line)
		else:
			show_custom_error("'[' section was expected.", token.line)

	elif token.family == 'TOKEN_leftBracket':
		lex()
		# {p1}
		R_true, R_false = condition()
		if token.family == 'TOKEN_rightBracket':
			lex()
		else:
			show_custom_error("']' was expected.", token.line)
	else:
		e1_place = expression()
		if token.value in ['==','<','>','!=','<=','>=']:
			cur_op = token.value
			lex()
			e2_place = expression()
		else:
			show_custom_error(f"logical operator was expected.", token.line)

		# {p1}
		R_true = make_list(next_quad())
		gen_quad(cur_op, e1_place, e2_place, '_') # Where to go if true
		R_false = make_list(next_quad())
		gen_quad('jump', '_', '_', '_') # Where to go if false

	return R_true, R_false

def while_stat():
	# {p1}
	cond_quad = next_quad()
	lex()
	if token.family == "TOKEN_leftParenthesis":
		lex()
		B_true, B_false = condition()
		if token.family == "TOKEN_rightParenthesis":
			# {p2}
			backpatch(B_true, next_quad())

			lex()
			if token.family == "TOKEN_colon":
				lex()
				if token.family == "TOKEN_left_hashbracket":
					lex()
					statements()
					if token.family == "TOKEN_right_hashbracket":
						lex()	
					else:
						error(token.line,"#}")
				else:
					statement()

				# {p3}
				gen_quad('jump', '_', '_', cond_quad)
				backpatch(B_false, next_quad())
			else:
				error(token.line,":")
		else:
			error(token.line,")")
	else:
		error(token.line,"(")


def call_main_part():
	if token.family == "TOKEN_if":
		lex()
		if token.value == '__name__':
			lex()
			if token.family == "TOKEN_equal":
				lex()
				if token.value == '”__main__”':
					lex()
					if token.family == 'TOKEN_colon':
						lex()
						while(token.family == "TOKEN_id"):
							if token.value[:5] != "main_":
								show_custom_error(f"'{token.value}' is not a valid main function name.\n"+
												 "\tMain function names should always start with 'main_'.",
												 token.line)

							gen_quad('call', token.value, '_', '_')
							main_function_call()


def main_function_call():
	lex()
	if token.family == "TOKEN_leftParenthesis":
		lex()
		if token.family == "TOKEN_rightParenthesis":
			lex()
			if token.family == "TOKEN_semiColon":
				lex()

#-----------------------------------------------------#

#------------------- FINAL CODE -------------------#

def gnlvcode(v):
	e, l = symbols_table.search_record(v)
	num_levels_remaining = symbols_table.get_current_scope_level() - 1 - l

	produce("lw t0, -4(sp)") # Go to parent scope
	for _ in range(num_levels_remaining):
		produce("lw t0, -4(t0)")

	produce(f"addi t0, t0, -{e.get_offset()}")


def loadvr(v, reg):

	# Case constant
	if v.isdigit():
		produce(f"li {reg}, {v}")
		return

	e, l = symbols_table.search_record(v)

	if l == symbols_table.get_current_scope_level(): # Case 1: Variable/Parameter/Temporary variable in CURRENT scope
		produce(f"lw {reg}, -{e.get_offset()}(sp)")
	else: # Case 2: Variable/Parameter/Temporary variable in PARENT scope
		gnlvcode(v)
		produce(f"lw {reg}, (t0)")


def storerv(reg, v):

	e, l = symbols_table.search_record(v)

	if l == symbols_table.get_current_scope_level(): # Case 1: Variable/Parameter/Temporary variable in CURRENT scope
		produce(f"sw {reg}, -{e.get_offset()}(sp)")
	else: # Case 2: Variable/Parameter/Temporary variable in PARENT scope
		gnlvcode(v)
		produce(f"sw {reg}, (t0)")


def produce(asm_command, tab=True):
	if tab:
		asm_f.write('\t' + asm_command + '\n')
	else:
		asm_f.write(asm_command + '\n')


#--------------------------------------------------#

def generate_int_code():
	for q in quad_list:
		int_f.write(q.__str__() + '\n')


param_cnt = 0 # Global variable to keep count of parameters when a function is called

def generate_final_code():
	global param_cnt

	generate_int_code()

	for q in quad_list:
		produce(f"L{q.get_q_id()}:", tab=False)
		if q.get_op() == '=':
			loadvr(q.get_x(), 't5')
			storerv('t5', q.get_z())
		elif q.get_op() in ['+', '-', '*', '//']:
			loadvr(q.get_x(), 't1')
			loadvr(q.get_y(), 't2')
			produce(f"{operations_code_dict[q.get_op()]} t1, t1, t2")
			storerv('t1', q.get_z())
		elif q.get_op() == 'out':
			loadvr(q.get_x(), 'a0')
			produce("li a7, 1")
			produce("ecall")

			# Print newline
			produce("la a0, str_nl")
			produce("li a7, 4")
			produce("ecall")
		elif q.get_op() == 'in':
			produce("li a7, 5")
			produce("ecall")

			# Store from a0 to variable
			storerv('a0', q.get_x())
		elif q.get_op() == 'jump':
			produce(f"j L{q.get_z()}")
		elif q.get_op() in ['==','<','>','!=','<=','>=']:
			loadvr(q.get_x(), 't1')
			loadvr(q.get_y(), 't2')
			produce(f"{cond_jump_code_dict[q.get_op()]} t1, t2, L{q.get_z()}")
		elif q.get_op() == 'par':
			if param_cnt == 0:
				# Find name of function to be called to get framelength
				for q_temp in quad_list[quad_list.index(q):]:
					if q_temp.get_op() == 'call':
						func_name = q_temp.get_x()

				e, _ =  symbols_table.search_record(func_name)
				produce(f"addi fp, sp, {e.get_framelength()}")

			# Store parameter value in activation record of function
			if q.get_y() == 'cv':
				loadvr(q.get_x(), 't0')
				produce(f"sw t0, -{3*MEM_BLOCK_SIZE + param_cnt*MEM_BLOCK_SIZE}(fp)")
			elif q.get_y() == 'ret':
				e, _ =  symbols_table.search_record(q.get_x())

				produce(f"addi t0, sp, -{e.get_offset()}")
				produce("sw t0, -8(fp)")

			param_cnt += 1
		elif q.get_op() == 'ret':
			loadvr(q.get_x(), "t1")

			produce("lw t0, -8(sp)")
			# produce(f"lw t1, -{e.get_offset()}(sp)")
			produce("sw t1, (t0)")
		elif q.get_op() == 'call':
			e, l = symbols_table.search_record(q.get_x())

			# If no parameters, move fp
			if param_cnt == 0:
				produce(f"addi fp, sp, {e.get_framelength()}")

			if l == symbols_table.get_current_scope_level(): # Call of child function
				produce("sw sp, -4(fp)")
			else: # Call of sibling/self function
				produce('lw t0, -4(sp)')
				produce('sw t0, -4(fp)')

			# Move sp
			produce(f"addi sp, sp, {e.get_framelength()}")
			produce(f"jal L{e.get_starting_quad()}")
			produce(f"addi sp, sp, -{e.get_framelength()}")

			param_cnt = 0 # Reset parameters counter
		elif q.get_op() == 'begin_block':
			if symbols_table.get_current_scope_level() > 0:
				produce(f"{q.get_x()}:", tab=False)
				produce("sw ra, (sp)")
			else:
				produce(f"{filename.split('.')[0]}:", tab=False)
				produce(f"addi sp, sp, {3*MEM_BLOCK_SIZE + symbols_table.get_cur_scope_var_num()}")
		elif q.get_op() == 'end_block':
			if symbols_table.get_current_scope_level() > 0:
				produce("lw ra, (sp)")
				produce("jr ra")
		elif q.get_op() == 'halt':
			produce("li a0, 0")
			produce("li a7, 93")
			produce("ecall")


	quad_list.clear()


def main():
	global int_f, asm_f

	open_cpy_file()

	# Create and open code files
	int_f = open('.'.join(filename.split('.')[:-1]) + '.int', 'w')
	asm_f = open('.'.join(filename.split('.')[:-1]) + '.asm', 'w')

	# Produce some introductory code lines
	produce(".data", tab=False)
	produce("str_nl: .asciz " + r'"\n"')
	produce(".text\n", tab=False)
	produce("L0:", tab=False)
	produce(f"j {filename[:-4]}")

	parser()

	# # Print quad list
	# print("\n#----------- QUADS -----------#")
	# for q in quad_list: print(q)

	# Close files
	file.close()
	int_f.close()
	asm_f.close()



main()
