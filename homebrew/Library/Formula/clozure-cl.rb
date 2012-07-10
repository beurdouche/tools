require 'formula'
require 'find'

class ClozureCl < Formula
  url 'ftp://ftp.clozure.com/pub/release/1.8/ccl-1.8-darwinx86.tar.gz'
  version '1.8'
  homepage 'http://ccl.clozure.com/'
  md5 'ff235d9cec6f45502e993096c80570b9'

  def install
    # Get rid of all the .svn dirs, that for some reason are
    # included in the tarball
    Find.find(buildpath) do |path|
      if File.directory?(path) && File.basename(path) == '.svn'
        rm_rf path
        Find.prune
      end
    end

    # Due to the way ClozureCL is organized, we'll put everything into
    # a subdirectory, and then link all the necessary scripts to the
    # locations Homebrew expects
    ccl_install_dir = prefix + 'ccl'

    # These scripts allow the user to execute some code or get a REPL
    ccl_scripts = Dir['./scripts/ccl{,64}']

    # ClozureCL uses the CCL_DEFAULT_DIRECTORY to find its sources. Update
    # it so it points to the right directory (since the ccl scripts themselves
    # won't be in the usual location)
    ccl_scripts.map { |path| Pathname.new(File.expand_path(path)) }.each do |script|
      inreplace script do |s|
        s.gsub! /CCL_DEFAULT_DIRECTORY=.+$/, %Q{CCL_DEFAULT_DIRECTORY="#{ccl_install_dir}"}
      end
    end

    # Copy everything over to the cellar
    ccl_install_dir.install Dir['*']

    # Link the wrapper scripts to prefix/bin, where Homebrew can link them properly
    bin.mkdir
    ccl_scripts.each do |script|
      ln ccl_install_dir+script, bin+File.basename(script)
    end
  end

  def caveats
    <<-CAVEATS
    Run `ccl` to run a 32-bit session, and `ccl64` for a 64-bit one.

    To test if everything works correctly, run `brew test #{name}`.
    CAVEATS
  end

  # Generates a string to test the ccl scripts that can be passed directly to `system'
  def test_ccl(bit = 32)
    ccl = bin + "ccl#{'64' if bit == 64}"
    %Q{#{ccl} -e '(progn (format t "Hello world from #{bit}-bit ClozureCL") (ccl::quit))'}
  end

  def test
    system test_ccl
    system test_ccl(64)
  end
end
