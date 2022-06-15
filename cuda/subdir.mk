################################################################################
# Automatically-generated file. Do not edit!
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
CU_SRCS += \
../src/nanoBraggCUDA.cu 

C_SRCS += \
../src/nanoBragg.c \
../src/nanoBraggCPU.c 

OBJS += \
./src/nanoBragg.o \
./src/nanoBraggCPU.o \
./src/nanoBraggCUDA.o 

CU_DEPS += \
./src/nanoBraggCUDA.d 

C_DEPS += \
./src/nanoBragg.d \
./src/nanoBraggCPU.d 


# Each subdirectory must supply rules for building sources it contributes
src/%.o: ../src/%.c
	@echo 'Building file: $<'
	@echo 'Invoking: NVCC Compiler'
	/usr/local/cuda-9.1/bin/nvcc -lineinfo -O3 -maxrregcount 32 -gencode arch=compute_35,code=sm_35 -gencode arch=compute_61,code=sm_61  -odir "src" -M -o "$(@:%.o=%.d)" "$<"
	/usr/local/cuda-9.1/bin/nvcc -lineinfo -O3 -maxrregcount 32 --compile  -x c -o  "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '

src/%.o: ../src/%.cu
	@echo 'Building file: $<'
	@echo 'Invoking: NVCC Compiler'
	/usr/local/cuda-9.1/bin/nvcc -lineinfo -O3 -maxrregcount 32 -gencode arch=compute_35,code=sm_35 -gencode arch=compute_61,code=sm_61  -odir "src" -M -o "$(@:%.o=%.d)" "$<"
	/usr/local/cuda-9.1/bin/nvcc -lineinfo -O3 -maxrregcount 32 --compile --relocatable-device-code=false -gencode arch=compute_35,code=compute_35 -gencode arch=compute_61,code=compute_61 -gencode arch=compute_35,code=sm_35 -gencode arch=compute_61,code=sm_61  -x cu -o  "$@" "$<"
	@echo 'Finished building: $<'
	@echo ' '


