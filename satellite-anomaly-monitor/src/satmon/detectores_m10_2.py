"""Detectores pontuais de M10.2; matrizes de entrada sem rótulos."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from threadpoolctl import threadpool_limits


def erro_pca_por_amostra(x, centro, componentes):
    """Soma dos resíduos quadráticos por linha. Componentes PCA nas linhas."""
    x, centro, componentes = (np.asarray(a, dtype=float) for a in (x, centro, componentes))
    if x.ndim != 2 or not len(x) or centro.shape != (x.shape[1],):
        raise ValueError("Esperados x [n, p] não vazio e centro [p].")
    if componentes.ndim != 2 or componentes.shape[1] != x.shape[1] or not len(componentes):
        raise ValueError("Esperados componentes PCA [k, p] não vazios.")
    if not all(np.isfinite(a).all() for a in (x, centro, componentes)):
        raise ValueError("Projeção exige valores finitos.")
    centrado = x - centro
    coordenadas = centrado @ componentes.T
    reconstruido = coordenadas @ componentes + centro
    return np.square(x - reconstruido).sum(axis=1)


def conferir_projecao(funcao):
    """Contas geométricas; uma base rotacionada pega erros de orientação."""
    mu = np.array([9.0, -1.0])
    w = np.array([[1.0, 1.0]]) / np.sqrt(2.0)
    x = np.array([[10.0, 0.0], [9.0, -1.0], [11.0, -3.0], [8.0, 0.0]])
    for a in (x, mu, w):
        a.setflags(write=False)
    resultado = np.asarray(funcao(x, mu, w))
    np.testing.assert_allclose(resultado, [0.0, 0.0, 8.0, 2.0], atol=1e-12, rtol=0)

    mu = np.array([2.0, 5.0, -3.0])
    w = np.array([[1.0, 0.0, 0.0], [0.0, 2**-0.5, 2**-0.5]])
    x = np.array([[1.0, 3.0, 2.0], [2.0, 4.0, -4.0], [-30.0, 5.0, -3.0]])
    resultado = np.asarray(funcao(x, mu, w))
    np.testing.assert_allclose(resultado, [24.5, 0.0, 0.0], atol=1e-12, rtol=0)


@dataclass
class Detectores:
    mediana: np.ndarray
    escala: np.ndarray
    pca: PCA
    floresta: IsolationForest
    contextos: KMeans

    @classmethod
    def ajustar(cls, x_ajuste, config):
        """Escala, PCA, árvores e centros aprendidos somente no ajuste."""
        mediana = np.median(x_ajuste, axis=0)
        mad = np.median(np.abs(x_ajuste - mediana), axis=0)
        escala = 1.4826 * mad
        if not np.isfinite(escala).all() or (escala <= 0).any():
            raise ValueError("Um canal tem MAD nulo ou inválido no ajuste.")
        x = (x_ajuste - mediana) / escala
        with threadpool_limits(limits=2):
            pca = PCA(n_components=config["pca_components"], svd_solver="full").fit(x)
            floresta = IsolationForest(
                n_estimators=config["forest_trees"], max_samples=config["forest_max_samples"],
                contamination="auto", random_state=config["random_state"], n_jobs=2,
            ).fit(x)
            contextos = KMeans(
                n_clusters=config["kmeans_clusters"], n_init=config["kmeans_n_init"],
                random_state=config["random_state"], algorithm="lloyd",
            ).fit(x)
        return cls(mediana, escala, pca, floresta, contextos)

    def pontuar(self, x, funcao_pca):
        z = (x - self.mediana) / self.escala
        with threadpool_limits(limits=2):
            projetado = self.pca.transform(z)
            reconstruido = self.pca.inverse_transform(projetado)
            esperado = np.square(z - reconstruido).sum(axis=1)
            insumos = [a.view() for a in (z, self.pca.mean_, self.pca.components_)]
            for a in insumos:
                a.setflags(write=False)
            pca = np.asarray(funcao_pca(*insumos), dtype=float)
            if pca.shape != esperado.shape:
                raise ValueError(f"A função PCA deve devolver um escore por linha: {esperado.shape}.")
            np.testing.assert_allclose(pca, esperado, rtol=1e-10, atol=1e-12,
                                       err_msg="Reconstrução manual divergiu de transform/inverse_transform.")
            return {
                "score_robusto": np.abs(z).max(axis=1),
                "score_pca": pca,
                "score_isolation": -self.floresta.score_samples(z),
                "grupo_kmeans": self.contextos.predict(z),
            }, float(np.abs(pca - esperado).max())
