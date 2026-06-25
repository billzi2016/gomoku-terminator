from __future__ import annotations


def main() -> int:
    """列出当前开局库采用的公开参考来源。

    RenjuNet 页面适合用作 26 标准开局形的官方参考，但页面标注 All rights
    reserved，因此脚本不会自动抓取和再分发网页图片或深度棋谱内容。
    """

    print("opening sources:")
    print("- RenjuNet 26 Renju Openings: https://www.renju.net/openings/")
    print("- RenjuNet Starting the Game: https://www.renju.net/starting/")
    print("- direct opening diagram: https://www.renju.net/upload/staticfiles/direct_openings.png")
    print("- indirect opening diagram: https://www.renju.net/upload/staticfiles/indirect_openings.png")
    print("")
    print("note: deep SGF/RenLib opening data must be imported only from sources with clear redistribution terms.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
