-- Official Lean 4.35.0 supports forms deliberately excluded from .ps.
def structuralExample (n : Nat) : Nat := n
termination_by structural n

def withNativeMeasure (n : Nat) : Nat := n
termination_by n
decreasing_by omega
