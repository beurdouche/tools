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
#include "Utils.h"
#include "Volumes.h"
#include <string.h>
#include <getopt.h>
#include <stdio.h>
#include <stdlib.h>
#include "Core.h"

/* The name of this program.*/
const char *program_name;


/* Prints usage information for this program to STREAM (typically
stdout or stderr), and exit the program with EXIT_CODE. Does not
return. */
void print_usage (FILE* stream, int exit_code)
{
    fprintf (stream,  "Bruteforce password cracker for Truecrypt volume.\n"
             "Optimazed with Nvidia Cuda technology.\n"
	     "Based on TrueCrypt, freely available at http://www.truecrypt.org/\n"
             "Copyright (c) 2011 by Luca Vaccaro\n"
            );

    fprintf (stream, "Usage: %s options [ inputfile | value ] volumefile\n", program_name);
    fprintf (stream,
             " -h --help            Display this usage information.\n"
             " -t --truecrypt FILE  Truecrypt volume file.\n"
             " -w --wordlist FILE   Wordlist mode, read words from FILE.\n"
	     " -m --maxlength INT   Charset mode, max length of words generated.\n"
             " -c --charset STRING  Charset mode, create words from charset STRING.\n"
	     " -b --blocksize INT   Block size of words parallel computed.\n"
             " -v --verbose         Show cracked passwords.\n"
            );
    exit (exit_code);
}

/* Main program entry point. ARGC contains number of argument list
elements; ARGV is an array of pointers to them. */
int main (int argc, char* argv[])
{
    int next_option;
    /* A string listing valid short options letters.*/
    const char* const short_options = "ht:w:c:m:b:v";
    /* An array describing valid long options. */
    const struct option long_options[] = {
        { "help", 0, NULL, 'h' },
        { "truecrypt",1,NULL, 't'},
        { "wordlist",1, NULL, 'w' },
        { "charset",1, NULL, 'c' },
	{ "maxlength",1, NULL, 'm' },
	{ "blocksize",1,NULL, 'b' },
        { "verbose", 0, NULL, 'v' },
        { NULL, 0, NULL, 0 }
        /* Required at end of array.
        */
    };
    /* The name of the file of words */
    const char* wordlist_filename = NULL;
    /* The name of the file of truecrypt volume */
    const char* volume_filename = NULL;
    /* The charset string */
    const char* charset = NULL;
    /*The max length of words generated from charset */
    int charsetmaxlength=0;
    /* The type of attack */
    int typeAttack=-1;
    /* Size of the block of parallel words*/
    int blocksize=0;
    /* Whether to display verbose messages. */
    int verbose = 0;
    /* Remember the name of the program, to incorporate in messages.
    The name is stored in argv[0]. */
    program_name = argv[0];
    do {
        next_option = getopt_long (argc, argv, short_options, long_options, NULL);
        switch (next_option)
        {
        case 'h':
            /* -h or --help */
            /* User has requested usage information. Print it to standard
            output, and exit with exit code zero (normal termination). */
            print_usage (stdout, 0);
        case 't':
            /* -t or --truecrypt */
            /* This option takes an argument, the name of the truecrypt volume.*/
            volume_filename = optarg;
            break;
        case 'w':
            /* -w or --wordlist */
            /* This option takes an argument, the name of the wordlist file.*/
            wordlist_filename = optarg;
            typeAttack=0;
            break;
        case 'c':
            /* -c or --charset */
            /* This option takes an argument, the charset string*/
            charset = optarg;
            typeAttack=1;
            break;
        case 'm':
            /* -m or --maxlength */
            /* This option takes an argument, the maxlength of generated words*/
            charsetmaxlength = atoi(optarg);
            typeAttack=1;
            break;
        case 'b':
            blocksize = atoi(optarg);
            break;
        case 'v':
            verbose = 1;
            break;
        case '?':
            /* The user specified an invalid option. */
            /* Print usage information to standard error, and exit with exit
            code one (indicating abnormal termination). */
            print_usage (stderr, 1);
        case -1:
            break;
            /* Done with options.
            */
        default:
            /* Something else: unexpected.*/
            abort ();
        }

    } while (next_option != -1);

    /*
     * The main program goes here.
    */
    CORE_verbose=verbose;
    CORE_blocksize=blocksize;
    if (volume_filename!=NULL)
        CORE_volumePath=volume_filename;
    else
        print_usage (stdout, 0);

    if (typeAttack==0) {
        CORE_typeAttack=ATTACK_DICTIONARY;
        if (wordlist_filename!=NULL)
            CORE_wordsPath=wordlist_filename;
        else
            print_usage (stdout, 0);
    } else if (typeAttack==1) {
        CORE_typeAttack=ATTACK_CHARSET;
        if (charset!=NULL)
            CORE_charset=charset;
        else
            print_usage (stdout, 0);
	if (charsetmaxlength>0)
	    CORE_charsetmaxlength=charsetmaxlength;
	 else
            print_usage (stdout, 0);
	
    } else
        print_usage (stdout, 0);



    core();

    return 0;
}

