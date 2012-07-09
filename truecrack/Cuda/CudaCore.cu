/*
 * Copyright (C)  2011  Luca Vaccaro
 *
 * TrueCrack is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 3
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
 *
 */

#include "Tcdefs.h"
#include "Volumes.h"
#include <stdio.h>
#include <memory.h>
#include "Crypto.h"
#include "CudaCore.cuh"
#include "CudaPkcs5.cuh"
#include "CudaXts.cuh"



/* The max number of block grid; number of max parallel gpu blocks. */
int blockGridSizeMax;

/* The number of the current block grid; number of current parallel gpu blocks. */
int blockGridSizeCurrent;

/* Pointer of structures to pass to Cuda Kernel. */
unsigned char *dev_salt, *dev_blockPwd, *dev_header;
int *dev_blockPwd_init, *dev_blockPwd_length;
short int *dev_result;


int getMultiprocessorCount (void){
	cudaDeviceProp prop;
	cudaGetDeviceProperties(&prop,0);
	return prop.multiProcessorCount;
}

__global__ void cuda_Kernel ( unsigned char *salt, unsigned char *headerEncrypted, unsigned char *blockPwd, int *blockPwd_init, int *blockPwd_length, short int *result) {

    int numData=blockIdx.x;
    int numBlock=threadIdx.x;

    // Array of unsigned char in the shared memory
    __shared__ __align__(8) unsigned char headerkey[192];
    __shared__ __align__(8) unsigned char headerDecrypted[512];
    
    
    // Calculate the hash header key
    cuda_Pbkdf2 (salt, blockPwd, blockPwd_init, blockPwd_length, headerkey, numData, numBlock);

    // Synchronize all threads in the block
    __syncthreads();
    
    // Decrypt the header and compare the key
    if (numBlock==0) {
        int value;
        value=cuda_Xts (headerEncrypted, headerkey,headerDecrypted);

        if (value==SUCCESS)
            result[numData]=MATCH;
        else
            result[numData]=NOMATCH;
    }
    //__syncthreads();
}
void cuda_Core ( short int *result) {


    cudaMalloc ( &dev_result, blockGridSizeCurrent * sizeof(short int)) ;
    cudaMemcpy( dev_result, result, blockGridSizeCurrent * sizeof(short int) , cudaMemcpyHostToDevice) ;

    cuda_Kernel<<<blockGridSizeCurrent,10>>>(dev_salt, dev_header, dev_blockPwd, dev_blockPwd_init, dev_blockPwd_length, dev_result);
    //cudaThreadSynchronize();

    cudaMemcpy(result, dev_result,blockGridSizeCurrent * sizeof(short int) , cudaMemcpyDeviceToHost) ;
}


void cuda_Init (int block_maxsize, unsigned char *salt, unsigned char *header) {
    blockGridSizeMax=block_maxsize;

    cudaMalloc ( (void **)&dev_blockPwd, blockGridSizeMax * PASSWORD_MAXSIZE * sizeof(unsigned char)) ;
    cudaMalloc ( (void **)&dev_blockPwd_init, blockGridSizeMax * sizeof(int)) ;
    cudaMalloc ( (void **)&dev_blockPwd_length, blockGridSizeMax * sizeof(int)) ;
    cudaMalloc ( (void **)&dev_salt, SALT_LENGTH * sizeof(unsigned char)) ;
    cudaMalloc ( (void **)&dev_header, TC_VOLUME_HEADER_EFFECTIVE_SIZE * sizeof(unsigned char)) ;
    cudaMalloc ( (void **)&dev_result, blockGridSizeMax * sizeof(short int)) ;

    cudaMemcpy(dev_salt, salt, SALT_LENGTH * sizeof(unsigned char) , cudaMemcpyHostToDevice) ;
    cudaMemcpy(dev_header, header, TC_VOLUME_HEADER_EFFECTIVE_SIZE * sizeof(unsigned char) , cudaMemcpyHostToDevice) ;

}

void cuda_Set (	int block_currentsize, unsigned char *blockPwd, int *blockPwd_init, int *blockPwd_length, short int *result) {

    blockGridSizeCurrent=block_currentsize;
    int lengthpwd=0,i;
    for (i=0;i<blockGridSizeCurrent;i++) {
        lengthpwd+=blockPwd_length[i];
        result[i]=NODEFINED;
    }

    cudaMemcpy(dev_blockPwd, blockPwd, lengthpwd * sizeof(unsigned char) , cudaMemcpyHostToDevice) ;
    cudaMemcpy(dev_blockPwd_init, blockPwd_init, blockGridSizeCurrent * sizeof(int) , cudaMemcpyHostToDevice) ;
    cudaMemcpy(dev_blockPwd_length, blockPwd_length, blockGridSizeCurrent * sizeof(int) , cudaMemcpyHostToDevice) ;
    cudaMemcpy(dev_result, result, blockGridSizeCurrent * sizeof(short int) , cudaMemcpyHostToDevice) ;
}


void cuda_Free(void) {
    cudaFree(dev_salt);
    cudaFree(dev_blockPwd);
    cudaFree(dev_blockPwd_init);
    cudaFree(dev_blockPwd_length);
    cudaFree(dev_result);
    cudaFree(dev_header);
}
