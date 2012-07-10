require 'formula'

class Netpbm < Formula
  homepage 'http://netpbm.sourceforge.net'
  url 'http://sourceforge.net/projects/netpbm/files/super_stable/10.35.82/netpbm-10.35.82.tgz'
  md5 'fcae2fc7928ad7d31b0540ec0c3e710b'

  head 'http://netpbm.svn.sourceforge.net/svnroot/netpbm/trunk'

  depends_on "libtiff"
  depends_on "jasper"
  depends_on :libpng

  def install
    if ARGV.build_head?
      system "cp", "config.mk.in", "config.mk"
      config = "config.mk"
    else
      system "cp", "Makefile.config.in", "Makefile.config"
      config = "Makefile.config"
    end

    inreplace config do |s|
      s.remove_make_var! "CC"
      s.change_make_var! "CFLAGS_SHLIB", "-fno-common"
      s.change_make_var! "NETPBMLIBTYPE", "dylib"
      s.change_make_var! "NETPBMLIBSUFFIX", "dylib"
      s.change_make_var! "LDSHLIB", "--shared -o $(SONAME)"
      s.change_make_var! "TIFFLIB", "-ltiff"
      s.change_make_var! "JPEGLIB", "-ljpeg"
      s.change_make_var! "PNGLIB", "-lpng"
      s.change_make_var! "ZLIB", "-lz"
      s.change_make_var! "JASPERLIB", "-ljasper"
      s.change_make_var! "JASPERHDR_DIR", "#{HOMEBREW_PREFIX}/include/jasper"
    end

    ENV.deparallelize
    system "make"
    system "make", "package", "pkgdir=#{buildpath}/stage"
    cd 'stage' do
      prefix.install %w{ bin include lib misc }
      # do man pages explicitly; otherwise a junk file is installed in man/web
      man1.install Dir['man/man1/*.1']
      man5.install Dir['man/man5/*.5']
      lib.install Dir['link/*.a']
    end
  end
end
