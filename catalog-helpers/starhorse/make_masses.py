# Standard library
import pathlib

# Third-party
import astropy.table as at
import astropy.units as u
import h5py
import numpy as np
import thejoker as tj
from schwimmbad.utils import batch_tasks
from scipy.stats import truncnorm as _truncnorm

from hq.config import Config
from hq.log import logger
from hq.physics_helpers import fast_m2_min, fast_mf


def truncnorm(mu, sigma, clip_a, clip_b):
    a, b = (clip_a - mu) / sigma, (clip_b - mu) / sigma
    return _truncnorm(loc=mu, scale=sigma, a=a, b=b)


def worker(task):
    conf = task['conf']

    percentiles = [1, 5, 16, 50, 84, 95, 99]
    n_m1 = 16  # number of M1 samples to produce per Joker/MCMC sample

    new_rows = []
    with h5py.File(conf.joker_results_file, 'r') as joker_f, \
         h5py.File(conf.mcmc_results_file, 'r') as mcmc_f:

        for row in task['metadata']:
            if np.isnan(row['mass1']) or row['mass1_err'] <= 0:
                continue

            source_id = str(row['APOGEE_ID']).strip()

            if 0 < row['mcmc_status'] <= 2:
                results_f = mcmc_f
            else:
                results_f = joker_f

            samples = tj.JokerSamples.read(
                results_f[f'{source_id}'], path='samples')

            m1_samples = truncnorm(
                row['mass1'], row['mass1_err'],
                0, 1e2).rvs(size=(len(samples), n_m1)).ravel() * u.Msun
            mf = fast_mf(samples['P'], samples['K'], samples['e'])
            mf = np.repeat(mf.value[:, None], n_m1, axis=1).ravel() * mf.unit

            m2_min = fast_m2_min(m1_samples.to_value(mf.unit),
                                 mf.value) * mf.unit

            new_row = {
                'APOGEE_ID': row['APOGEE_ID'],
                'mass1_50': row['mass1'] * u.Msun,
                'mass1_err': row['mass1_err'] * u.Msun
            }
            for pp in percentiles:
                new_row[f'mass2_min_{pp}'] = np.nanpercentile(m2_min, pp)
            new_rows.append(new_row)

    if len(new_rows) == 0:
        return None
    else:
        return at.QTable(new_rows)


def main(run_path, pool, overwrite, seed):
    output_path = pathlib.Path(__file__).resolve().parent
    output_file = output_path / 'starhorse_mass_m2_min.fits'

    if output_file.exists() and not overwrite:
        logger.warn(f'Output file exists at {output_file!s}')
        return

    conf = Config(run_path / 'config.yml')
    meta = at.QTable.read(conf.metadata_file, hdu=1)

    starhorse_file = (
        '/mnt/home/apricewhelan/data/APOGEE_DR17/'
        'APOGEE_DR17_EDR3_STARHORSE_v1.fits'
    )
    sh = at.Table.read(starhorse_file)
    meta_sh = at.join(meta, sh, keys='APOGEE_ID', join_type='left')

    # Primary masses and uncertainties from starhorse:
    meta_sh['mass1'] = meta_sh['mass50'].filled(np.nan)
    err = np.max([
        meta_sh['mass1'] - meta_sh['mass16'],
        meta_sh['mass84'] - meta_sh['mass1']
    ], axis=0)
    meta_sh['mass1_err'] = err

    tasks = []
    for i1, i2 in batch_tasks(4 * pool.size, len(meta_sh)):
        tasks.append({
            'conf': conf,
            'metadata': meta_sh[i1:i2]
        })

    results = []
    for res in pool.map(worker, tasks):
        if res is not None:
            results.append(res)

    result_table = at.vstack(results)
    result_table.write(output_file, overwrite=True)


if __name__ == '__main__':
    import sys
    from threadpoolctl import threadpool_limits
    from hq.cli.helpers import get_parser

    parser = get_parser(loggers=[logger])

    parser.add_argument("-s", "--seed", dest="seed", default=None,
                        type=int, help="Random number seed")
    args = parser.parse_args(sys.argv[2:])

    if args.seed is None:
        args.seed = np.random.randint(2**32 - 1)
        logger.log(
            1, f"No random seed specified, so using seed: {args.seed}")

    with threadpool_limits(limits=1, user_api='blas'):
        with args.Pool(**args.Pool_kwargs) as pool:
            main(run_path=args.run_path,
                 pool=pool,
                 overwrite=args.overwrite,
                 seed=args.seed)

    sys.exit(0)
