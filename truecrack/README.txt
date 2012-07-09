TRUECRACK
TrueCrack is a bruteforce password cracker for TrueCrypt (Copyrigth) volume.
It is optimazed with Nvidia Cuda technology.
It works with PBKDF2 (defined in PKCS5 v2.0) based on RIPEMD160 Key derivation 
function and XTS block cipher mode of operation used for hard disk encryption 
based on AES.

LICENSE
TrueCrack is an Open Source Software under GNU Public License version 3.
This software is Based on TrueCrypt, freely available at http://www.truecrypt.org/

AUTHOR
The author Luca Vaccaro is an graduate student of Politecnico di Milano in 
Engineering Informatics.

COMPILE
The software can work on CPU or GPU. 
If you want the Cuda optimization, you set the GPU variable on true:
   make GPU=true
Else if you want use only the CPU resource, you set the GPU variable on false:
   make GPU=false
