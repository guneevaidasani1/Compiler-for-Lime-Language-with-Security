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
  store i32 10, i32* %".2"
  %".4" = bitcast [5 x i8]* @"__str_1" to i8*
  %".5" = bitcast [18 x i8]* @"__str_2" to i8*
  %".6" = call i32 (i8*, ...) @"printf"(i8* %".4", i8* %".5")
  %".7" = load i32, i32* %".2"
  %".8" = icmp sle i32 %".7", 0
  br i1 %".8", label %"main_entry.if", label %"main_entry.endif"
main_entry.if:
  %".10" = bitcast [5 x i8]* @"__str_3" to i8*
  %".11" = bitcast [39 x i8]* @"__str_4" to i8*
  %".12" = call i32 (i8*, ...) @"printf"(i8* %".10", i8* %".11")
  ret i32 1
main_entry.endif:
  %".14" = alloca i32
  store i32 0, i32* %".14"
  %".16" = alloca i32
  store i32 1, i32* %".16"
  %".18" = load i32, i32* %".2"
  %".19" = icmp sge i32 %".18", 1
  br i1 %".19", label %"main_entry.endif.if", label %"main_entry.endif.endif"
main_entry.endif.if:
  %".21" = load i32, i32* %".14"
  %".22" = bitcast [5 x i8]* @"__str_5" to i8*
  %".23" = call i32 (i8*, ...) @"printf"(i8* %".22", i32 %".21")
  br label %"main_entry.endif.endif"
main_entry.endif.endif:
  %".25" = load i32, i32* %".2"
  %".26" = icmp sge i32 %".25", 2
  br i1 %".26", label %"main_entry.endif.endif.if", label %"main_entry.endif.endif.endif"
main_entry.endif.endif.if:
  %".28" = load i32, i32* %".16"
  %".29" = bitcast [5 x i8]* @"__str_6" to i8*
  %".30" = call i32 (i8*, ...) @"printf"(i8* %".29", i32 %".28")
  br label %"main_entry.endif.endif.endif"
main_entry.endif.endif.endif:
  %".32" = alloca i32
  store i32 2, i32* %".32"
  br label %"for_loop_entry_7"
for_loop_entry_7:
  %".35" = load i32, i32* %".14"
  %".36" = load i32, i32* %".16"
  %".37" = add i32 %".35", %".36"
  %".38" = alloca i32
  store i32 %".37", i32* %".38"
  %".40" = load i32, i32* %".38"
  %".41" = bitcast [5 x i8]* @"__str_8" to i8*
  %".42" = call i32 (i8*, ...) @"printf"(i8* %".41", i32 %".40")
  %".43" = load i32, i32* %".16"
  store i32 %".43", i32* %".14"
  %".45" = load i32, i32* %".38"
  store i32 %".45", i32* %".16"
  %".47" = load i32, i32* %".32"
  %".48" = add i32 %".47", 1
  store i32 %".48", i32* %".32"
  %".50" = load i32, i32* %".32"
  %".51" = load i32, i32* %".2"
  %".52" = icmp slt i32 %".50", %".51"
  br i1 %".52", label %"for_loop_entry_7", label %"for_loop_otherwise_7"
for_loop_otherwise_7:
  ret i32 0
}

@"__str_1" = internal constant [5 x i8] c"%s\0a\00\00"
@"__str_2" = internal constant [18 x i8] c"Fibonacci Series:\00"
@"__str_3" = internal constant [5 x i8] c"%s\0a\00\00"
@"__str_4" = internal constant [39 x i8] c"Please enter a positive integer for N.\00"
@"__str_5" = internal constant [5 x i8] c"%d\0a\00\00"
@"__str_6" = internal constant [5 x i8] c"%d\0a\00\00"
@"__str_8" = internal constant [5 x i8] c"%d\0a\00\00"