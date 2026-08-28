# -*- coding: utf-8 -*-
"""
AIDA Standalone Self-Healing CLI
================================
Django server ishlamayotgan bo'lsa ham tizimni skanerlaydi va to'g'irlaydi.
"""
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent))

# Set settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AIDA.settings")

from self_improvement.diagnostics import run_full_diagnostics
from self_improvement.code_fixer import fix_all_errors

def main():
    print("=" * 60)
    print("AIDA STANDALONE SELF-HEALING SYSTEM")
    print("=" * 60)

    # 1. Run Diagnostics
    print("\n[1] Tizim diagnostikasi ishlamoqda...")
    report = run_full_diagnostics()
    summary = report["summary"]

    print(f"  Sintaksis xatolar: {summary['syntax_errors']}")
    print(f"  Log xatolar:       {summary['log_issues']}")
    print(f"  DB holati:         {'OK' if summary['db_ok'] else 'XATO'}")
    print(f"  Tizim sog'lom:     {report['healthy']}")

    # 2. Fix Errors if found
    if not report["healthy"] and summary["syntax_errors"] > 0:
        print("\n[2] Xatolarni avtomatik to'g'irlash boshlandi (Gemini AI)...")
        fix_results = fix_all_errors(report["syntax_errors"])
        
        fixed_count = sum(1 for r in fix_results if r["fixed"])
        print(f"  Natija: {fixed_count}/{len(fix_results)} ta fayl muvaffaqiyatli to'g'irlandi.")
        
        for r in fix_results:
            status = "MUVAFFAQIYAT" if r["fixed"] else "MUVAFFAQIYATSIZ"
            print(f"    - [{status}] {Path(r['filepath']).name}: {r['message']}")

        # 3. Re-run Diagnostics
        print("\n[3] Qayta tekshirish...")
        report2 = run_full_diagnostics()
        if report2["healthy"]:
            print("\n  TABRIKLAYMIZ! Tizim o'z-o'zini to'liq sog'lomlashtirdi.")
        else:
            print("\n  Hali ham xatoliklar mavjud.")
    else:
        print("\n[OK] Tizim to'liq sog'lom, hech qanday xato topilmadi.")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
