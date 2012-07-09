OBJS_COMMON = \
Volumes.o \
Crc.o\
Endian.o 

OBJ_MAIN = \
Core.o \
Charset.o \
Utils.o \
Main.o

OBJS_CRYPTO =

CFLAGS = -I./Common/ -I./Crypto/ -I./Cuda/ -I./Main/ -I./ -lm

ifeq "$(DEBUG)" "true"
	CFLAGS += -D_DEBUG_
endif

ifeq "$(GPU)" "true"
	OBJ_CUDA=Cuda.o
	CC=nvcc
	CFLAGS += -D_GPU_
	OBJS_COMMON += #gpuCrypto.o
else
	OBJS_CRYPTO += Rmd160.o CpuAes.o 
	OBJS_COMMON += Pkcs5.o CpuCore.o

endif


all: truecrack

truecrack:  $(OBJ_CUDA) $(OBJ_MAIN) $(OBJS_COMMON) $(OBJS_CRYPTO) 
	$(CC) -o $@ $(OBJ_CUDA) $(OBJS_COMMON) $(OBJ_MAIN) $(OBJS_CRYPTO) $(CFLAGS)

$(OBJ_CUDA): 
	cat Cuda/CudaCore.cu > Cuda.cu 
	cat Cuda/CudaPkcs5.cu >> Cuda.cu
	cat Cuda/CudaRmd160.cu >> Cuda.cu
	cat Cuda/CudaAes.cu >> Cuda.cu
	cat Cuda/CudaXts.cu >> Cuda.cu
	$(CC) -c Cuda.cu $(CFLAGS) --opencc-options -OPT:Olimit=0 $< -o $@

$(OBJS_COMMON): %.o: Common/%.c
	$(CC) -c $(CFLAGS) $< -o $@

$(OBJS_CRYPTO): %.o: Crypto/%.c
	$(CC) -c $(CFLAGS) $< -o $@

$(OBJ_MAIN): %.o: Main/%.c
	$(CC) -c $(CFLAGS) $< -o $@


clean:
	rm -rf truecrack
	rm -rf *.o *.cu
