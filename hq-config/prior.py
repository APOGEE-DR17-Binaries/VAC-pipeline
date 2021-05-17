# Imports we typically need for defining the prior:
import astropy.units as u
import pymc3 as pm
import exoplanet.units as xu
from pymc3_ext.distributions import Angle
import numpy as np
import thejoker as tj
import theano.tensor as tt


defaults = {
    'P_min': 1.5 * u.day,
    'P_max': 16384 * u.day,
    'sigma_v': 100 * u.km/u.s,
    'sigma_K0': 30 * u.km/u.s,
    'logs_mean': -3.5,
    'logs_std': 1.
}


def get_prior(**kwargs):
    for k, v in defaults.items():
        kwargs.setdefault(k, v)

    with pm.Model() as model:
        s = xu.with_unit(
            pm.Lognormal('s', kwargs['logs_mean'], kwargs['logs_std']),
            u.km/u.s
        )

        prior = tj.JokerPrior.default(
            P_min=kwargs['P_min'], P_max=kwargs['P_max'],
            sigma_K0=kwargs['sigma_K0'],
            sigma_v=kwargs['sigma_v'],
            s=s
        )

    return prior, model


def get_prior_mcmc(MAP_sample, fixed_s=False, **kwargs):
    for k, v in defaults.items():
        kwargs.setdefault(k, v)

    with pm.Model() as model:
        lnP = pm.Uniform('lnP',
                         np.log(kwargs['P_min'].to_value(u.day)),
                         np.log(kwargs['P_max'].to_value(u.day)))
        P = xu.with_unit(
            pm.Deterministic('P', tt.exp(lnP)),
            u.day)

        if fixed_s is False:
            s = pm.Bound(pm.Lognormal, 0, 5.)('s',
                                              kwargs['logs_mean'],
                                              kwargs['logs_std'])
            s = xu.with_unit(s, u.km/u.s)
        else:
            s = fixed_s

        if MAP_sample['e'] < 0.1:
            omega_p_M0 = Angle('omega_p_M0')
            omega_m_M0 = Angle('omega_m_M0')
            omega = xu.with_unit(
                pm.Deterministic('omega', 0.5 * (omega_p_M0 + omega_m_M0)),
                u.radian
            )
            M0 = xu.with_unit(
                pm.Deterministic('M0', 0.5 * (omega_p_M0 - omega_m_M0)),
                u.radian
            )

        else:
            omega = xu.with_unit(Angle('omega'), u.radian)
            M0 = xu.with_unit(Angle('M0'), u.radian)

        pm.Deterministic('t_peri', P * M0 / (2*np.pi))

        prior_mcmc = tj.JokerPrior.default(
            sigma_K0=kwargs['sigma_K0'],
            sigma_v=kwargs['sigma_v'],
            s=s,
            pars={'P': P, 'M0': M0, 'omega': omega}
        )

        # ecc = prior_mcmc.pars['e']
        def get_phase(f, M0, e):
            E = 2 * tt.arctan(tt.sqrt((1 - e) / (1 + e)) * tt.tan(0.5 * f))
            M = E - e * tt.sin(E)
            return (M + M0) % (2 * np.pi)

        pm.Deterministic('phase_rv_max', get_phase(-omega, M0,
                                                   prior_mcmc.pars['e']))
        pm.Deterministic('phase_rv_min', get_phase(np.pi - omega, M0,
                                                   prior_mcmc.pars['e']))

    return prior_mcmc, model


def custom_init_mcmc(mcmc_init, MAP_sample, model):
    mcmc_init['lnP'] = np.log(mcmc_init['P'])
    mcmc_init['omega_p_M0'] = mcmc_init['omega'] + mcmc_init['M0']
    mcmc_init['omega_m_M0'] = mcmc_init['omega'] - mcmc_init['M0']

    mcmc_init = {k: v
                 for k, v in mcmc_init.items()
                 if k in model.named_vars.keys()}

    return mcmc_init
