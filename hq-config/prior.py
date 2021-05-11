# Imports we typically need for defining the prior:
import astropy.coordinates as coord
import astropy.units as u
import pymc3 as pm
import exoplanet.units as xu
from exoplanet.distributions import Angle
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


def pick_M0_omega_parametrization(MAP_sample, model):
    wrap = np.pi * u.rad
    M0 = coord.Angle(MAP_sample['M0']).wrap_at(wrap)
    omega = coord.Angle(MAP_sample['omega']).wrap_at(wrap)
    M0_m_omega = coord.Angle(M0 - omega).wrap_at(wrap)
    M0_p_omega = coord.Angle(M0 + omega).wrap_at(wrap)

    angles = np.array([x.radian for x in [M0, omega, M0_m_omega, M0_p_omega]])
    angle_names = np.array(['M0', 'omega', 'M0_m_omega', 'M0_p_omega'])

    angle_names = set(angle_names[np.argsort(np.abs(angles))][:2])

    with model:
        if angle_names == {'M0', 'omega'}:
            M0 = xu.with_unit(Angle('M0'), u.radian)
            omega = xu.with_unit(Angle('omega'), u.radian)

        elif angle_names == {'M0', 'M0_m_omega'}:
            M0 = xu.with_unit(Angle('M0'), u.radian)
            M0_m_omega = xu.with_unit(Angle('M0_m_omega'), u.radian)
            omega = xu.with_unit(
                pm.Deterministic('omega', M0 - M0_m_omega),
                u.radian)

        elif angle_names == {'M0', 'M0_p_omega'}:
            M0 = xu.with_unit(Angle('M0'), u.radian)
            M0_p_omega = xu.with_unit(Angle('M0_p_omega'), u.radian)
            omega = xu.with_unit(
                pm.Deterministic('omega', M0_p_omega - M0),
                u.radian)

        elif angle_names == {'omega', 'M0_m_omega'}:
            omega = xu.with_unit(Angle('omega'), u.radian)
            M0_m_omega = xu.with_unit(Angle('M0_m_omega'), u.radian)
            M0 = xu.with_unit(
                pm.Deterministic('M0', M0_m_omega + omega),
                u.radian)

        elif angle_names == {'omega', 'M0_p_omega'}:
            omega = xu.with_unit(Angle('omega'), u.radian)
            M0_p_omega = xu.with_unit(Angle('M0_p_omega'), u.radian)
            M0 = xu.with_unit(
                pm.Deterministic('M0', M0_p_omega - omega),
                u.radian)

        elif angle_names == {'M0_m_omega', 'M0_p_omega'}:
            M0_m_omega = xu.with_unit(Angle('M0_m_omega'), u.radian)
            M0_p_omega = xu.with_unit(Angle('M0_p_omega'), u.radian)
            M0 = xu.with_unit(
                pm.Deterministic('M0', 0.5 * (M0_p_omega + M0_m_omega)),
                u.radian)
            omega = xu.with_unit(
                pm.Deterministic('omega', 0.5 * (M0_p_omega - M0_m_omega)),
                u.radian)

        else:
            raise ValueError('TODO')

    return M0, omega


def get_prior_mcmc(MAP_sample=None, fixed_s=False, **kwargs):
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

        # When running MCMC, we will sample in the parameters
        #     (M0 - omega, M0 + omega) instead of (M0, omega)
        # M0_m_omega = xu.with_unit(Angle('M0_m_omega'), u.radian)
        # omega = xu.with_unit(Angle('omega'), u.radian)
        # M0 = xu.with_unit(pm.Deterministic('M0', M0_m_omega + omega),
        #                   u.radian)

        if MAP_sample is not None:
            # Auto-determine what parametrization to use based on MAP sample
            M0, omega = pick_M0_omega_parametrization(MAP_sample, model)

        else:
            M0 = xu.with_unit(Angle('M0'), u.radian)
            omega = xu.with_unit(Angle('omega'), u.radian)

        prior_mcmc = tj.JokerPrior.default(
            sigma_K0=kwargs['sigma_K0'],
            sigma_v=kwargs['sigma_v'],
            s=s,
            pars={'P': P, 'M0': M0, 'omega': omega}
        )

    return prior_mcmc, model
