# Standard library
import pathlib

# Third-party
import astropy.coordinates as coord
import astropy.table as at
from astropy.time import Time
import astropy.units as u
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import thejoker as tj
from schwimmbad.utils import batch_tasks

from hq.config import Config
from hq.log import logger


def plot_diagnostic(c, row, allstar, mcmc=True):
    source_id = row['APOGEE_ID']

    data, joker_samples, joker_MAP_s = c.get_data_samples(source_id)
    if mcmc:
        _, samples, MAP_s = c.get_data_samples(source_id, mcmc=True)

        P_mask = samples['P'] < 0.5*u.day
        if P_mask.sum():
            samples = samples[~P_mask]
            print(f"Source {row['APOGEE_ID']} has samples with P < 0.5 day")
    else:
        MAP_s = joker_MAP_s

    # Also plot VRELERR error bars...
    visits = c.data[c.data['APOGEE_ID'] == source_id]
    data_vrelerr = tj.RVData(
        Time(visits['JD'], format='jd', scale='tdb'),
        visits['VHELIO']*u.km/u.s,
        visits['VRELERR']*u.km/u.s)

    max_t_grid = 8192  # MAGIC NUMBER
    fig, all_axes = plt.subplots(3, 3, figsize=(16, 12),
                                 constrained_layout=True)

    axes = all_axes[0]
    _ = tj.plot_rv_curves(joker_MAP_s, data=data, ax=axes[0],
                          plot_kwargs=dict(zorder=50, color='tab:blue'),
                          data_plot_kwargs=dict(zorder=100),
                          max_t_grid=max_t_grid)  # HACK
    _ = data_vrelerr.plot(ax=axes[0], add_labels=False,
                          color='tab:green', zorder=99, marker='')

    if mcmc:
        _ = tj.plot_rv_curves(samples[:128], data=data, ax=axes[0],
                              plot_kwargs=dict(zorder=10),
                              data_plot_kwargs=dict(alpha=0),
                              max_t_grid=max_t_grid)
    _ = tj.plot_phase_fold(MAP_s, data=data, ax=axes[1],
                           remove_trend=False, with_time_unit=True)
    axes[1].set_ylim(axes[0].get_ylim())

    _ = tj.plot_phase_fold(MAP_s, data=data, ax=axes[2],
                           remove_trend=False, residual=True,
                           with_time_unit=True)
    axes[2].axhline(0, color='tab:green', alpha=0.4, zorder=-10)

    axes[1].set_yticklabels([])
    axes[1].set_ylabel('')
    axes[2].set_ylabel('')

    fig.suptitle(row['APOGEE_ID'], fontsize=20)

    axes[0].set_title("raw time series", fontsize=18)
    axes[1].set_title("phase-folded", fontsize=18)
    axes[2].set_title("residual", fontsize=18)

    #################
    # Other metadata:
    axes = all_axes[1]

    # CMD:
    ax = axes[0]
    plx_snr = row['GAIAEDR3_PARALLAX'] / row['GAIAEDR3_PARALLAX_ERROR']
    if row['M_H'] > -2.5 and plx_snr > 4:
        plx_snr = (allstar['GAIAEDR3_PARALLAX'] /
                   allstar['GAIAEDR3_PARALLAX_ERROR'])
        mask = ((np.abs(allstar['M_H'] - row['M_H']) < 0.2) &
                (plx_snr > 6) &
                (allstar['J'] > -999) &
                (allstar['K'] > -999))

        dist = coord.Distance(parallax=row['GAIAEDR3_PARALLAX']*u.mas)
        mag_row = row['J'] - dist.distmod.value
        col_row = row['J'] - row['K']

        dist = coord.Distance(
            parallax=allstar['GAIAEDR3_PARALLAX'][mask] * u.mas)
        mag = allstar['J'][mask] - dist.distmod.value
        col = allstar['J'][mask] - allstar['K'][mask]

        ax.hist2d(col, mag,
                  bins=(np.arange(-0.1, 1.5, 0.02),
                        np.arange(-5, 8, 0.04)),
                  cmap='Blues', norm=mpl.colors.LogNorm())
        ax.errorbar(col_row, mag_row,
                    marker='o', ls='none',
                    color='tab:red', alpha=0.8)

    ax.set_xlabel('$J-K$')
    ax.set_ylabel('$M_J$')
    ax.set_xlim(-0.1, 1.5)
    ax.set_ylim(8, -5)

    # Period-Eccentricity
    ax = axes[1]
    if mcmc:
        ax.plot(samples['P'].value, samples['e'].value,
                marker='o', ls='none', mew=0, ms=2, alpha=0.7,
                color='k')
    ax.plot(joker_samples['P'].value, joker_samples['e'].value,
            marker='o', ls='none', mew=0, ms=2, alpha=0.7,
            color='tab:blue')
    ax.set_xlim(1, 3e3)
    ax.set_ylim(0, 1)
    ax.set_xscale('log')
    ax.set_xlabel('period $P$')
    ax.set_ylabel('eccentricity $e$')

    # Mass / m2_min
    ax = axes[2]
    if np.isfinite(row['mass1_50']):
        ax.scatter(row['mass1_50'], row['mass2_min_50'],
                   marker='o', s=12, zorder=100)
        ax.plot([row['mass1_50'].value, row['mass1_50'].value],
                [row['mass2_min_16'].value, row['mass2_min_84'].value],
                marker='', color='tab:blue', zorder=50)
        ax.plot([row['mass1_50'].value, row['mass1_50'].value],
                [row['mass2_min_1'].value, row['mass2_min_99'].value],
                marker='', color='tab:red', zorder=25)

        grid = np.geomspace(1e-3, 1e2, 128)
        ax.plot(grid, grid, marker='', ls='--', color='#aaaaaa', zorder=0)

        ax.set_xlabel(f'$M_1$ [{u.Msun:latex_inline}]')
        ax.set_ylabel(r'$M_{2, {\rm min}}$ ' + f'[{u.Msun:latex_inline}]')

        ax.axhline(0.08, ls='-', color='tab:green', zorder=0, alpha=0.6)

        ax.set_xlim(0, 3)
        ax.set_yscale('log')
        ax.set_ylim(1e-3, 1e2)
    else:
        ax.set_visible(False)

    ############
    # Text info:
    axes = all_axes[2]
    for ax in axes:
        ax.xaxis.set_visible(False)
        ax.yaxis.set_visible(False)
        ax.set(xlim=(0, 1), ylim=(0, 1))

    ax = axes[0]
    text = (
        "Joker log-like".rjust(18) +
        f"  ${row['max_unmarginalized_ln_likelihood']:.3f}$\n" +
        "const log-like".rjust(18) +
        f"  ${row['robust_constant_ln_likelihood']:.3f}$\n" +
        "linear log-like".rjust(18) +
        f"  ${row['robust_linear_ln_likelihood']:.3f}$\n\n" +
        "Teff".rjust(8) + f"  ${row['TEFF']:.0f}$\n" +
        "logg".rjust(8) + f"  ${row['LOGG']:.2f}$\n" +
        "[M/H]".rjust(8) + f"  ${row['M_H']:.3f}$\n" +
        "vsini".rjust(8) + f"  ${row['VSINI']:.1f}$\n" +
        "S/N".rjust(8) + f"  ${row['SNR']:.0f}$\n"
    )
    ax.text(0.05, 0.95, text,
            fontsize=14, va='top', ha='left',
            fontfamily='monospace')

    text = (
        f"RV_FLAG: {row['RV_FLAG']}\n" +
        f"N_COMPONENTS: {row['N_COMPONENTS']}"
    )
    ax.text(0.05, 0.05, text,
            fontsize=14, va='bottom', ha='left',
            fontfamily='monospace')

    # Flagging:
    ax = axes[1]
    ax.text(0.05, 0.95,
            "STARFLAGS:\n" + '\n'.join(row['STARFLAGS'].split(',')),
            fontsize=14, va='top', ha='left',
            fontfamily='monospace')
    ax.text(0.05, 0.05,
            "ASPCAPFLAGS:\n" + '\n'.join(row['ASPCAPFLAGS'].split(',')),
            fontsize=14, va='bottom', ha='left',
            fontfamily='monospace')

    # Sampling statistics:
    ax = axes[2]
    med_verr_ratio = np.nanmedian(visits['VRELERR'] / visits['CALIB_VERR'])
    text = (
        f"Joker completed: {str(row['joker_completed'])}\n" +
        f"MCMC converged: {str(row['gelman_rubin_max'] < 1.4)}\n" +
        f"Gelman-Rubin: {row['gelman_rubin_max']:.2f}\n" +
        f"Median VRELERR/CALIB_VERR: {med_verr_ratio:.2f}"
    )
    ax.text(0.05, 0.95, text,
            fontsize=14, va='top', ha='left',
            fontfamily='monospace')

    fig.set_facecolor('w')

    return fig


def worker(task):
    allstar = at.QTable.read(
        '/mnt/home/apricewhelan/data/APOGEE_DR17/allStar-dr17-synspec.fits',
        hdu=1)

    paths = []
    for row in task['metadata']:
        this_plot_path = task['plot_path'] / f"{row['APOGEE_ID']}.png"

        try:
            fig = plot_diagnostic(task['conf'], row, allstar)
        except Exception as e:  # noqa
            print(f"FAILED {row['APOGEE_ID']}: \n\t {e!s}")
            continue

        fig.savefig(this_plot_path, dpi=200)
        plt.close(fig)

        paths.append(this_plot_path)

    return paths


def make_gallery(www_path, paths):
    filenames = [p.name for p in paths]

    fmt_str_visible = "<a href='{path}' data-sub-html='#{captionid}'><img src='{path}' width='512px' /></a>"
    fmt_str_hidden = "<a href='{path}' data-sub-html='#{captionid}'><img src='{path}' style='display: none;' /></a>"
    a_img_links = []
    captions = []
    for i, path in enumerate(sorted(filenames)):
        captionid = f"caption{i}"
        apogee_id = path[:-4]

        if i < 1:
            a_img_links.append(fmt_str_visible.format(path=str(path),
                                                      captionid=captionid))
        else:
            a_img_links.append(fmt_str_hidden.format(path=str(path),
                                                     captionid=captionid))

        caption = f"""<div id='{captionid}' style='display:none'>
            <h2 id='h2_{i}'>{apogee_id}</h2>
            <button onclick="append_bad_id('{apogee_id}')">Bad Fit</button>
        </div>"""
        captions.append(caption)

    img_text = "\n\n".join(a_img_links)
    caption_text = "\n\n".join(captions)

    html_page = f'''
    <html>

    <head>
        <link rel="stylesheet" href="node_modules/lightgallery.js/dist/css/lightgallery.css">
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
    </head>

    <body>

    <script src="node_modules/lightgallery.js/dist/js/lightgallery.min.js"></script>
    <script src="node_modules/lg-thumbnail.js/dist/lg-thumbnail.min.js"></script>
    <script src="node_modules/lg-fullscreen.js/dist/lg-fullscreen.min.js"></script>

    <div style="font-size: 18pt; margin-bottom: 100px;">
        Click the first plot to open the gallery.
    </div>

    {caption_text}

    <div id="gallery">

    {img_text}

    </div>

    <div style="margin-top: 24px;">
        <button onclick="dump_bad_ids()">Log bad APOGEE_IDs (console)</button>
    </div>


    <script type="text/javascript">
            var el = document.getElementById("gallery")

            lightGallery(el, {{
                thumbnail: true,
                speed: 1,
                preload: 5,
                width: '80%'
            }});

            var bad_apogee_ids = new Array();
            var last_viewed_id = "";

            function append_bad_id(apogee_id) {{
                bad_apogee_ids.push(apogee_id);
            }}

            function dump_bad_ids() {{
                var idx = window.lgData[el.getAttribute('lg-uid')].index;
                console.log("Last viewed source: index = " + idx + ", id = " + last_viewed_id);
                console.log(bad_apogee_ids.join("' , '"));
            }}

            el.addEventListener('onAfterSlide', function(e) {{
                var hdr = document.getElementById("h2_" + event.detail.index);
                last_viewed_id = hdr.innerText;
            }}, false);

    </script>

    </body>

    </html>
    '''

    with open(www_path / 'index.html', 'w') as f:
        f.write(html_page)


def main(run_path, pool, overwrite, seed):
    project_path = pathlib.Path(
        '/mnt/home/apricewhelan/projects/apogee-dr17-binaries/'
    )
    plot_path = project_path / 'plots/unimodal'
    plot_path.mkdir(exist_ok=True)

    conf = Config(project_path / 'hq-config/config.yml')

    allstar = at.QTable.read(
        '/mnt/home/apricewhelan/data/APOGEE_DR17/allStar-dr17-synspec.fits',
        hdu=1)

    sh = at.Table.read(
        project_path / 'catalog-helpers/starhorse/starhorse_mass_m2_min.fits')

    metadata = at.QTable.read(conf.metadata_file)
    metadata = at.join(metadata, allstar, keys='APOGEE_ID')
    metadata = at.join(at.Table(metadata), at.Table(sh),
                       keys='APOGEE_ID', join_type='left')
    metadata = at.unique(metadata, keys='APOGEE_ID')

    # HACK: deal with the fact that QTable can't handle masking
    for col in metadata.colnames:
        if hasattr(metadata[col], 'mask') and np.any(metadata[col].mask):
            metadata[col] = metadata[col].filled(np.nan)
    metadata = at.QTable(metadata)

    # Select only good MCMC unimodal stars:
    good = metadata[(metadata['mcmc_status'] <= 2) &
                    (metadata['mcmc_completed'])]

    tasks = []
    for i1, i2 in batch_tasks(max(1, pool.size - 1), len(good)):
        tasks.append({
            'conf': conf,
            'metadata': good[i1:i2],
            'plot_path': plot_path
        })

    all_paths = []
    for paths in pool.map(worker, tasks):
        all_paths.append(paths)
    all_paths = [path for sublist in all_paths for path in sublist]

    make_gallery(plot_path, all_paths)


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
