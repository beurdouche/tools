require 'formula'

class Dwm < Formula
  url 'http://dl.suckless.org/dwm/dwm-6.0.tar.gz'
  homepage 'http://dwm.suckless.org/'
  md5 '8bb00d4142259beb11e13473b81c0857'
  head 'http://hg.suckless.org/dwm'

  def install
    # The dwm default quit keybinding Mod1-Shift-q collides with
    # the Mac OS X Log Out shortcut in the Apple menu.
    inreplace 'config.def.h',
    '{ MODKEY|ShiftMask,             XK_q,      quit,           {0} },',
    '{ MODKEY|ControlMask,           XK_q,      quit,           {0} },'
    inreplace 'dwm.1', '.B Mod1\-Shift\-q', '.B Mod1\-Control\-q'
    system "make", "PREFIX=#{prefix}", "install"
  end

  def caveats
    <<-EOS
    In order to use the Mac OS X command key for dwm commands,
    change the X11 keyboard modifier map using xmodmap (1).

    e.g. by running the following command from $HOME/.xinitrc
    xmodmap -e 'remove Mod2 = Meta_L' -e 'add Mod1 = Meta_L'&

    See also https://gist.github.com/311377 for a handful of tips and tricks
    for running dwm on Mac OS X.
    EOS
  end
end
