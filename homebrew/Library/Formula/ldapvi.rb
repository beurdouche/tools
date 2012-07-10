require 'formula'

class Ldapvi < Formula
  url 'http://www.lichteblau.com/download/ldapvi-1.7.tar.gz'
  homepage 'http://www.lichteblau.com/ldapvi/'
  md5 '6dc2f5441ac5f1e2b5b036e3521012cc'

  depends_on 'gettext'
  depends_on 'glib'
  depends_on 'popt'
  depends_on 'readline'

  def install
    system "./configure", "--prefix=#{prefix}", "--disable-dependency-tracking"
    system "make install"
  end

  # Backporting the fix from the devel version
  # (namespace conflict with Lion's getline function)
  # http://www.lichteblau.com/git/?p=ldapvi.git;a=commit;h=256ced029c235687bfafdffd07be7d47bf7af39b
  def patches
    DATA
  end

end

__END__
diff -rupN ldapvi-1.7-orig/common.h ldapvi-1.7-new/common.h
--- ldapvi-1.7-orig/common.h	2007-05-05 12:17:26.000000000 +0200
+++ ldapvi-1.7-new/common.h	2011-09-02 21:40:45.000000000 +0200
@@ -273,7 +273,7 @@ void pipeview_wait(int pid);
 char *home_filename(char *name);
 void read_ldapvi_history(void);
 void write_ldapvi_history(void);
-char *getline(char *prompt, char *value);
+char *ldapvi_getline(char *prompt, char *value);
 char *get_password();
 char *append(char *a, char *b);
 void *xalloc(size_t size);
diff -rupN ldapvi-1.7-orig/ldapvi.c ldapvi-1.7-new/ldapvi.c
--- ldapvi-1.7-orig/ldapvi.c	2007-05-05 12:17:26.000000000 +0200
+++ ldapvi-1.7-new/ldapvi.c	2011-09-02 21:41:17.000000000 +0200
@@ -470,7 +470,7 @@ change_mechanism(bind_options *bo)
 		bo->authmethod = LDAP_AUTH_SASL;
 		puts("Switching to SASL authentication.");
 	}
-	bo->sasl_mech = getline("SASL mechanism", bo->sasl_mech);
+	bo->sasl_mech = ldapvi_getline("SASL mechanism", bo->sasl_mech);
 }
 
 static int
diff -rupN ldapvi-1.7-orig/misc.c ldapvi-1.7-new/misc.c
--- ldapvi-1.7-orig/misc.c	2007-05-05 12:17:26.000000000 +0200
+++ ldapvi-1.7-new/misc.c	2011-09-02 21:41:45.000000000 +0200
@@ -315,7 +315,7 @@ write_ldapvi_history()
 }
 
 char *
-getline(char *prompt, char *value)
+ldapvi_getline(char *prompt, char *value)
 {
 	tdialog d;
 	init_dialog(&d, DIALOG_DEFAULT, prompt, value);
