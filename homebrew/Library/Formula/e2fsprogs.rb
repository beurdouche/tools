require 'formula'

class E2fsprogs < Formula
  homepage 'http://e2fsprogs.sourceforge.net/'
  url 'http://downloads.sourceforge.net/e2fsprogs/e2fsprogs-1.42.3.tar.gz'
  sha1 '0da8c787604876fe23b0f608389c3854ae1a2420'

  head 'https://git.kernel.org/pub/scm/fs/ext2/e2fsprogs.git'

  keg_only "This brew installs several commands which override OS X-provided file system commands."

  depends_on 'pkg-config' => :build

  def patches
    # MacPorts patch to compile libs correctly.
    p = {:p0 => [
      "https://trac.macports.org/export/92117/trunk/dports/sysutils/e2fsprogs/files/patch-lib__Makefile.darwin-lib"
    ]}

    # MacPorts patch to allow compilation on Leopard.
    if MacOS.leopard?
      p[:p0] << "https://trac.macports.org/export/92117/trunk/dports/sysutils/e2fsprogs/files/patch-lib-ext2fs-inline.c.diff"
    end

    p
  end

  def install
    ENV.append_to_cflags "--std=gnu89 -Wno-return-type" if ENV.compiler == :clang
    system "./configure", "--prefix=#{prefix}"
    system "make"
    system "make install"
    system "make install-libs"
  end
end
