require 'formula'

class Falcon < Formula
  homepage 'http://www.falconpl.org/'
  url 'http://falconpl.org/project_dl/_official_rel/Falcon-0.9.6.8.tgz'
  md5 '8435f6f2fe95097ac2fbe000da97c242'

  head 'http://git.falconpl.org/falcon.git'

  depends_on 'cmake' => :build
  depends_on 'pcre'

  def options
    [
      ['--editline', "Use editline instead of readline"],
      ['--feathers', "Include feathers (extra libraries)"]
    ]
  end

  def install
    args = ["-DCMAKE_BUILD_TYPE=Release",
            "-DCMAKE_INSTALL_PREFIX=#{prefix}",
            "-DFALCON_BIN_DIR=#{bin}",
            "-DFALCON_LIB_DIR=#{lib}",
            "-DFALCON_MAN_DIR=#{man1}",
            "-DFALCON_WITH_MANPAGES=ON",
            "-DFALCON_WITH_INTERNAL_PCRE=ON",
            "-DFALCON_WITH_INTERNAL_ZLIB=ON",
            "-DFALCON_WITH_INTERNAL=ON"]

    if ARGV.include? '--editline'
      args << "-DFALCON_WITH_EDITLINE=ON"
    else
      args << "-DFALCON_WITH_EDITLINE=OFF"
    end

    if ARGV.include? '--feathers'
      args << "-DFALCON_WITH_FEATHERS=feathers"
    else
      args << "-DFALCON_WITH_FEATHERS=NO"
    end

    system "cmake", *args
    system "make"
    system "make install"
  end
end
