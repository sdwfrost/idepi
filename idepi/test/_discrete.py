
import sys

from os import close, remove
from tempfile import mkstemp

import numpy as np

from BioExt.io import LazyAlignIO as AlignIO

from sklearn.svm import SVC

from sklmrmr import MRMR

from idepi.alphabet import Alphabet
from idepi.databuilder import DataBuilder
from idepi.filter import naivefilter
from idepi.labeler import Labeler
from idepi.util import (
    alignment_identify_refidx,
    is_refseq,
    seqrecord_get_ic50s,
    set_util_params
)

from ._common import (
    TEST_AMINO_STO,
    TEST_AMINO_NAMES,
    TEST_STANFEL_NAMES,
    TEST_Y,
    TEST_AMINO_X,
    TEST_STANFEL_X
)


__all__ = ['test_discrete']


def test_discrete(ARGS):
    # set these to this so we don't exclude anything (just testing file generation and parsing)
    ARGS.NUM_FEATURES = 15 # should be enough, the number is known to be 13
    ARGS.MRMR_METHOD = 'MID'
    ARGS.MAX_CONSERVATION = 1.0
    ARGS.MAX_GAP_RATIO    = 1.0
    ARGS.MIN_CONSERVATION = 1.0
    ARGS.CUTOFF = 20.

    # if we don't do this, DOOMBUNNIES
    set_util_params(ARGS.REFSEQ_IDS, ARGS.CUTOFF)

    fd, sto_filename = mkstemp(); close(fd)

    try:
        fh = open(sto_filename, 'w')
        print(TEST_AMINO_STO, file=fh)
        fh.close()

        alignment = AlignIO.read(sto_filename, 'stockholm')
        refidx = alignment_identify_refidx(alignment, is_refseq)

        for ARGS.ALPHABET in (Alphabet.AMINO, Alphabet.STANFEL):

            if ARGS.ALPHABET == Alphabet.STANFEL:
                TEST_NAMES = TEST_STANFEL_NAMES
                TEST_X = TEST_STANFEL_X
            else:
                TEST_NAMES = TEST_AMINO_NAMES
                TEST_X = TEST_AMINO_X

            alph = Alphabet(mode=ARGS.ALPHABET)

            filter = naivefilter(
                ARGS.MAX_CONSERVATION,
                ARGS.MIN_CONSERVATION,
                ARGS.MAX_GAP_RATIO,
            )
            builder = DataBuilder(
                alignment,
                alph,
                refidx,
                filter
            )
            x = builder(alignment, refidx)
            colnames = builder.labels

            # test the feature names portion
            try:
                assert(len(colnames) == len(TEST_NAMES))
            except AssertionError:
                raise AssertionError('gen:   %s\ntruth: %s' % (colnames, TEST_NAMES))

            for name in TEST_NAMES:
                try:
                    assert(name in colnames)
                except AssertionError:
                    raise AssertionError('ERROR: \'%s\' not found in %s' % (name, ', '.join(colnames)))

            assert(np.all(TEST_X == x))

            # test mRMR and LSVM file generation
            ylabeler = Labeler(
                seqrecord_get_ic50s,
                lambda row: is_refseq(row) or False, # TODO: again filtration function
                lambda x: x > ARGS.CUTOFF,
                False
            )
            y, ic50 = ylabeler(alignment)

            assert(np.all(TEST_Y == y))

            # generate and test the mRMR portion
            mrmr = MRMR(
                estimator=SVC(kernel='linear'),
                n_features_to_select=ARGS.NUM_FEATURES,
                method=ARGS.MRMR_METHOD,
                normalize=ARGS.MRMR_NORMALIZE,
                similar=ARGS.SIMILAR
                )

            mrmr.fit(x, y)

    finally:
        remove(sto_filename)

    print('ALL TESTS PASS', file=sys.stderr)


