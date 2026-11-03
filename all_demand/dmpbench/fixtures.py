from __future__ import annotations

from .model import Network


# Niu et al. (2020), Fig. 1. Edge order follows the paper.
NIU_FIG1 = Network.from_tuples(
    4,
    [(0, 1, 3), (0, 2, 2), (1, 3, 2), (1, 2, 1), (2, 3, 2)],
    0, 3, "niu_2020_fig1",
)
NIU_FIG1_D3 = {
    (1, 2, 1, 0, 2),
    (2, 1, 1, 1, 2),
    (2, 1, 2, 0, 1),
    (3, 0, 2, 1, 1),
}


# Lin et al. (1995), Example 1: three parallel branches represented as
# directed paths. Edge order matches the reported capacity vector.
LIN_EX1 = Network.from_tuples(
    4,
    [(0, 1, 1), (1, 3, 2), (0, 3, 2), (0, 2, 2), (2, 3, 1)],
    0, 3, "lin_1995_example1",
)
LIN_EX1_D2 = {
    (1, 1, 1, 0, 0),
    (1, 1, 0, 1, 1),
    (0, 0, 1, 1, 1),
    (0, 0, 2, 0, 0),
}


# A small cyclic directed network used for independent cross-checking.
CYCLIC_SMALL = Network.from_tuples(
    5,
    [(0, 1, 3), (0, 2, 2), (1, 2, 2), (2, 1, 2),
     (1, 3, 2), (2, 3, 2), (3, 4, 3), (2, 4, 1)],
    0, 4, "cyclic_small",
)


# Huang et al. (2020 final issue; 2019 early access), Fig. 3.
# The paper lists path sets without traversal order; the directed arcs are
# a1:s->upper, a2:upper->t, a3:upper->lower, a4:lower->upper,
# a5:s->lower, a6:lower->t.
HUANG_FIG3 = Network.from_tuples(
    4,
    [(0, 1, 2), (1, 3, 3), (1, 2, 2), (2, 1, 3), (0, 2, 3), (2, 3, 3)],
    0, 3, "huang_2020_fig3",
)
HUANG_FIG3_D4 = {
    (2, 2, 0, 0, 2, 2), (2, 3, 0, 1, 2, 1),
    (2, 1, 1, 0, 2, 3), (1, 1, 0, 0, 3, 3),
    (1, 2, 0, 1, 3, 2), (1, 3, 0, 2, 3, 1),
}


# Wu (2025), Fig. 2. The paper prints reconstructed vectors in ordered-
# variable order (e1,e5,e3,e4,e2,e6); expected vectors below are converted
# back to the canonical edge order (e1,e2,e3,e4,e5,e6).
WU_FIG2 = Network.from_tuples(
    4,
    [(0, 1, 3), (1, 3, 2), (1, 2, 1), (2, 1, 1), (0, 2, 1), (2, 3, 2)],
    0, 3, "wu_2025_fig2",
)
WU_FIG2_D3 = {
    (3, 2, 1, 0, 0, 1),
    (2, 1, 1, 0, 1, 2),
    (2, 2, 0, 0, 1, 1),
}


FIXTURES = {
    "lin_1995_example1": (LIN_EX1, 2, LIN_EX1_D2),
    "niu_2020_fig1": (NIU_FIG1, 3, NIU_FIG1_D3),
    "cyclic_small": (CYCLIC_SMALL, 3, None),
    "huang_2020_fig3": (HUANG_FIG3, 4, HUANG_FIG3_D4),
    "wu_2025_fig2": (WU_FIG2, 3, WU_FIG2_D3),
}

