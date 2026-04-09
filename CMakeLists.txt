cmake_minimum_required(VERSION 3.20)
project(AssemblyCourse NONE)

find_program(CLANG_EXECUTABLE clang REQUIRED)

if(APPLE AND CMAKE_HOST_SYSTEM_PROCESSOR STREQUAL "arm64")
	set(ASSEMBLY_TARGET_ARGS -target x86_64-apple-macos13)
else()
	set(ASSEMBLY_TARGET_ARGS)
endif()

function(add_assembly_lab target)
	set(output "${CMAKE_BINARY_DIR}/bin/${target}")

	add_custom_command(
		OUTPUT "${output}"
		COMMAND
			${CMAKE_COMMAND}
			-E
			make_directory
			"${CMAKE_BINARY_DIR}/bin"
		COMMAND
			${CLANG_EXECUTABLE}
			${ASSEMBLY_TARGET_ARGS}
			-Wall
			-Wextra
			-Wpedantic
			-std=c11
			${ARGN}
			-o
			"${output}"
		DEPENDS
			${ARGN}
		WORKING_DIRECTORY
			${CMAKE_SOURCE_DIR}
		VERBATIM
	)

	add_custom_target(${target} ALL DEPENDS "${output}")
endfunction()

add_assembly_lab(
	asm1_integer_calculator_starter
	"ASM1-Integer-Calculator/starter/main.c"
	"ASM1-Integer-Calculator/starter/calculator.S"
)
add_assembly_lab(
	asm1_integer_calculator_solution
	"ASM1-Integer-Calculator/solution/main.c"
	"ASM1-Integer-Calculator/solution/calculator.S"
)

add_assembly_lab(
	asm2_array_sum_search_starter
	"ASM2-Array-Sum-and-Search/starter/main.c"
	"ASM2-Array-Sum-and-Search/starter/array_routines.S"
)
add_assembly_lab(
	asm2_array_sum_search_solution
	"ASM2-Array-Sum-and-Search/solution/main.c"
	"ASM2-Array-Sum-and-Search/solution/array_routines.S"
)

add_assembly_lab(
	asm3_string_length_copy_starter
	"ASM3-String-Length-and-Copy/starter/main.c"
	"ASM3-String-Length-and-Copy/starter/string_routines.S"
)
add_assembly_lab(
	asm3_string_length_copy_solution
	"ASM3-String-Length-and-Copy/solution/main.c"
	"ASM3-String-Length-and-Copy/solution/string_routines.S"
)

add_assembly_lab(
	asm4_call_c_helper_starter
	"ASM4-Call-C-Helper-from-Assembly/starter/main.c"
	"ASM4-Call-C-Helper-from-Assembly/starter/helper.c"
	"ASM4-Call-C-Helper-from-Assembly/starter/scale_and_clamp.S"
)
add_assembly_lab(
	asm4_call_c_helper_solution
	"ASM4-Call-C-Helper-from-Assembly/solution/main.c"
	"ASM4-Call-C-Helper-from-Assembly/solution/helper.c"
	"ASM4-Call-C-Helper-from-Assembly/solution/scale_and_clamp.S"
)

add_assembly_lab(
	asm5_tiny_parser_starter
	"ASM5-Tiny-Command-Line-Parser/starter/main.c"
	"ASM5-Tiny-Command-Line-Parser/starter/parser.S"
)
add_assembly_lab(
	asm5_tiny_parser_solution
	"ASM5-Tiny-Command-Line-Parser/solution/main.c"
	"ASM5-Tiny-Command-Line-Parser/solution/parser.S"
)

add_assembly_lab(
	asm6_reverse_engineering_starter
	"ASM6-Reverse-Engineering-Toy-Program/starter/main.c"
	"ASM6-Reverse-Engineering-Toy-Program/starter/mystery.S"
	"ASM6-Reverse-Engineering-Toy-Program/starter/reconstructed.c"
)
add_assembly_lab(
	asm6_reverse_engineering_solution
	"ASM6-Reverse-Engineering-Toy-Program/solution/main.c"
	"ASM6-Reverse-Engineering-Toy-Program/solution/mystery.S"
	"ASM6-Reverse-Engineering-Toy-Program/solution/reconstructed.c"
)
