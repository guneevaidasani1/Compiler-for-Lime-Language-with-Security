; ModuleID = "main"
target triple = "x86_64-pc-windows-msvc"
target datalayout = ""

declare i32 @"printf"(i8* %".1", ...) noinline

@"true" = constant i1 1
@"false" = constant i1 0
define i32 @"main"()
{
main_entry:
  %".2" = alloca i32
  store i32 1, i32* %".2"
  %".4" = load i32, i32* %".2"
  %".5" = icmp slt i32 %".4", 1000000
  br i1 %".5", label %"while_loop_entry_1", label %"while_loop_otherwise_1"
while_loop_entry_1:
  %".7" = load i32, i32* %".2"
  %".8" = add i32 %".7", 1
  store i32 %".8", i32* %".2"
  %".10" = load i32, i32* %".2"
  %".11" = icmp slt i32 %".10", 1000000
  br i1 %".11", label %"while_loop_entry_1", label %"while_loop_otherwise_1"
while_loop_otherwise_1:
  %".13" = bitcast [7 x i8]* @"__str_2" to i8*
  %".14" = call i32 (i8*, ...) @"printf"(i8* %".13")
  ret i32 0
}

@"__str_2" = internal constant [7 x i8] c"Done\0a\00\00"