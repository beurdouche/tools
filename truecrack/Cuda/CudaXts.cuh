/*
 * Copyright (C)  2011  Luca Vaccaro
 * Based on TrueCrypt, freely available at http://www.truecrypt.org/
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
#ifndef CUDAXTS_H
#define CUDAXTS_H

// Header files (optional)

#include "Tcdefs.h"
#include "Common/Endian.h"
#include "Crypto.h"

//#include "CudaAes.cuh"


#ifdef __cplusplus
extern "C" {
#endif

// Macros

#ifndef LITTLE_ENDIAN
#	define LITTLE_ENDIAN	1
#endif

#ifndef BIG_ENDIAN
#	define BIG_ENDIAN		2
#endif

#ifndef BYTE_ORDER
#	define BYTE_ORDER		LITTLE_ENDIAN
#endif

#ifndef LE64
#	if BYTE_ORDER == LITTLE_ENDIAN
#		define LE64(x)	(x)
#	endif
#endif

// Custom data types
/*
#ifndef TC_LARGEST_COMPILER_UINT
#	ifdef TC_NO_COMPILER_INT64
		typedef unsigned __int32	TC_LARGEST_COMPILER_UINT;
#	else
		typedef unsigned __int64	TC_LARGEST_COMPILER_UINT;
#	endif
#endif
*/

#ifndef TCDEFS_H
typedef union 
{
	struct 
	{
		unsigned __int32 LowPart;
		unsigned __int32 HighPart;
	};
#	ifndef TC_NO_COMPILER_INT64
	unsigned __int64 Value;
#	endif

} UINT64_STRUCT;
#endif

// Public function prototypes

//void EncryptBufferXTS (unsigned __int8 *buffer, TC_LARGEST_COMPILER_UINT length, const UINT64_STRUCT *startDataUnitNo, unsigned int startCipherBlockNo, unsigned __int8 *ks, unsigned __int8 *ks2, int cipher);
//static void EncryptBufferXTSNonParallel (unsigned __int8 *buffer, TC_LARGEST_COMPILER_UINT length, const UINT64_STRUCT *startDataUnitNo, unsigned int startCipherBlockNo, unsigned __int8 *ks, unsigned __int8 *ks2, int cipher);
//void DecryptBufferXTS (unsigned __int8 *buffer, TC_LARGEST_COMPILER_UINT length, const UINT64_STRUCT *startDataUnitNo, unsigned int startCipherBlockNo, unsigned __int8 *ks, unsigned __int8 *ks2, int cipher);
//static void DecryptBufferXTSNonParallel (unsigned __int8 *buffer, TC_LARGEST_COMPILER_UINT length, const UINT64_STRUCT *startDataUnitNo, unsigned int startCipherBlockNo, unsigned __int8 *ks, unsigned __int8 *ks2, int cipher);

enum
{
  UNDEFINED,
  SUCCESS,
  ERR_OUT_OF_MEMORY,
  ERR_CIPHER_INIT,
  ERR_MODE_INIT,
  ERR_MAGIC_TRUE,
  ERR_VERSION_REQUIRED,
  ERR_CRC_HEADER_FIELDS,
  ERR_CRC_KEY_SET
};

enum{
  NODEFINED,
  MATCH,
  NOMATCH,
};




int cuda_Xts(unsigned char *encryptedHeader, unsigned char *headerKey, unsigned char *test);
int cuda_XtsTest(unsigned char *encryptedHeader, unsigned char *headerKey, unsigned char *test);

void cuda_DecryptBufferXTS (unsigned __int8 *buffer,
					   TC_LARGEST_COMPILER_UINT length,
					   unsigned int startCipherBlockNo,
					   unsigned __int8 *ks,
					   unsigned __int8 *ks2,
					   int cipher);

#ifdef __cplusplus
}
#endif

#endif	// #ifndef CUDAXTS_H
