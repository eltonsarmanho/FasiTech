"""
lancamento_service.py — Serviço de backend para matrícula e consolidação no SIGAA.

Usado pelo frontend Streamlit. Executa sempre sem janela de navegador (headless=True).

Exemplos de uso (dentro de contexto async — Streamlit usa asyncio):

1. Para atividades complementares (ACC):
    from lancamento_service import LancamentoService

    svc_acc = LancamentoService(
        matricula="202285940020",
        polo="OEIRAS DO PARÁ",
        periodo="2026.1",
        componente="ACC I",
    )

    resultado = await svc_acc.matricular()
    if resultado.sucesso:
        # st.success(resultado.mensagem)
        pass

    resultado = await svc_acc.consolidar(conceito="E")

2. Para Trabalho de Conclusão de Curso (TCC):
    svc_tcc = LancamentoService(
        matricula="202416040009",
        polo="CAMETÁ",
        periodo="2026.2",
        componente="TCC",
        orientador="ELTON SARMANHO SIQUEIRA", # OBRIGATORIO PARA TCC
    )

    resultado_tcc = await svc_tcc.matricular()
    resultado_cons_tcc = await svc_tcc.consolidar(conceito="E")
"""

import asyncio
from dataclasses import dataclass, field
from types import SimpleNamespace


# ── Resultado ─────────────────────────────────────────────────────────────────


@dataclass
class ResultadoOperacao:
    """Resultado retornado pelos métodos matricular() e consolidar()."""

    sucesso: bool
    mensagem: str
    detalhes: list[str] = field(default_factory=list)


# ── Serviço ───────────────────────────────────────────────────────────────────


class LancamentoService:
    """
    Serviço de backend que automatiza matrícula e consolidação no SIGAA via Playwright.

    O navegador é executado SEMPRE em modo headless (sem janela visível), adequado
    para uso em servidores e backends Streamlit.

    Parâmetros
    ----------
    matricula  : str  — Matrícula do aluno (ex: "202285940020")
    polo       : str  — Nome do polo (ex: "OEIRAS DO PARA")
    periodo    : str  — Período acadêmico (ex: "2026.1")
    componente : str  — Sigla do componente: ACC I, ACC II, ACC III, ACC IV, TCC, TCC I, TCC II
    executar   : bool — Se False, faz dry-run (navega, preenche, mas NÃO confirma).
                        Padrão True (executa de fato).

    Raises
    ------
    ValueError — se o componente informado não for válido.
    """

    COMPONENTES_VALIDOS = {"ACC I", "ACC II", "ACC III", "ACC IV", "TCC", "TCC I", "TCC II"}

    def __init__(
        self,
        matricula: str,
        polo: str,
        periodo: str,
        componente: str,
        orientador: str | None = None,
        executar: bool = True,
    ) -> None:
        componente_upper = componente.strip().upper()
        if componente_upper not in self.COMPONENTES_VALIDOS:
            validos = ", ".join(sorted(self.COMPONENTES_VALIDOS))
            raise ValueError(
                f"Componente inválido: '{componente}'. "
                f"Use um de: {validos}"
            )

        self.matricula = matricula.strip()
        self.polo = polo.strip()
        self.periodo = periodo.strip()
        self.componente = componente_upper
        self.orientador = (orientador or "").strip()
        self.executar = executar

        if self._is_tcc() and not self.orientador:
            raise ValueError("Orientador é obrigatório para lançamentos de TCC.")

    # ── Helpers internos ──────────────────────────────────────────────────────

    def _is_tcc(self) -> bool:
        return self.componente.startswith("TCC")

    def _args_matricular(self) -> SimpleNamespace:
        """Constrói o namespace de argumentos esperado por executar_fluxo_direto."""
        args = SimpleNamespace(
            matricula=self.matricula,
            polo=self.polo,
            periodo=self.periodo,
            componente=self.componente,
            curso=None,           # usa polo para localizar o curso no dropdown
            atividade_nome=None,  # usa o nome padrão do MAPA_COMPONENTE
            executar=self.executar,
            headless=True,        # sem janela de navegador — obrigatório para backend
            manter_aberto=False,
        )
        if self._is_tcc():
            args.orientador = self.orientador
        return args

    def _args_consolidar(self, conceito: str) -> SimpleNamespace:
        """Constrói o namespace de argumentos esperado por executar_consolidacao."""
        return SimpleNamespace(
            matricula=self.matricula,
            polo=self.polo,
            periodo=self.periodo,
            componente=self.componente,
            conceito=conceito.strip().upper(),
            curso=None,
            executar=self.executar,
            headless=True,
            manter_aberto=False,
        )

    # ── Operações principais ──────────────────────────────────────────────────

    async def matricular(self) -> ResultadoOperacao:
        """
        Realiza a matrícula do aluno no componente via SIGAA.

        Fluxo interno (sigaa_Matricular.py):
          Login → Selecionar Período → Portal Coord. Graduação →
          Selecionar Curso/Polo → Menu Atividades > Matricular →
          Buscar Discente → Selecionar Componente → Confirmar

        Returns
        -------
        ResultadoOperacao
            sucesso=True  → matrícula realizada (ou simulada em dry-run)
            sucesso=False → falha, com mensagem e detalhes do erro
        """
        try:
            if self._is_tcc():
                try:
                    from src.services.sigaa_Matricular_TCC import executar_fluxo_direto
                except ModuleNotFoundError:
                    from sigaa_Matricular_TCC import executar_fluxo_direto
            else:
                try:
                    from src.services.sigaa_Matricular import executar_fluxo_direto
                except ModuleNotFoundError:
                    from sigaa_Matricular import executar_fluxo_direto
        except ModuleNotFoundError as exc:
            raise RuntimeError("Não foi possível importar o serviço de matrícula do SIGAA.") from exc

        args = self._args_matricular()
        try:
            await executar_fluxo_direto(args)
            acao = "simulada (dry-run)" if not self.executar else "concluída com sucesso"
            return ResultadoOperacao(
                sucesso=True,
                mensagem=(
                    f"Matrícula de {self.matricula} em '{self.componente}' "
                    f"(polo: {self.polo} | período: {self.periodo}) {acao}."
                ),
            )
        except Exception as exc:
            return ResultadoOperacao(
                sucesso=False,
                mensagem=f"Erro na matrícula: {exc}",
                detalhes=[repr(exc)],
            )

    async def consolidar(self, conceito: str = "E") -> ResultadoOperacao:
        """
        Consolida a matrícula do aluno atribuindo o conceito informado.

        Fluxo interno (sigaa_Consolidar.py):
          Login → Selecionar Período → Portal Coord. Graduação →
          Selecionar Curso/Polo → Menu Atividades > Consolidar Matrículas →
          Localizar Discente + Componente → Selecionar Conceito → Confirmar

        Parameters
        ----------
        conceito : str
            Conceito a atribuir (ex: "E", "A", "B", "C", "D"). Padrão: "E".

        Returns
        -------
        ResultadoOperacao
            sucesso=True  → consolidação realizada (ou simulada em dry-run)
            sucesso=False → falha, com mensagem e detalhes do erro
        """
        try:
            if self._is_tcc():
                try:
                    from src.services.sigga_Consolidar_TCC import executar_consolidacao
                except ModuleNotFoundError:
                    from sigga_Consolidar_TCC import executar_consolidacao
            else:
                try:
                    from src.services.sigaa_Consolidar import executar_consolidacao
                except ModuleNotFoundError:
                    from sigaa_Consolidar import executar_consolidacao
        except ModuleNotFoundError as exc:
            raise RuntimeError("Não foi possível importar o serviço de consolidação do SIGAA.") from exc

        args = self._args_consolidar(conceito)
        try:
            await executar_consolidacao(args)
            acao = "simulada (dry-run)" if not self.executar else "concluída com sucesso"
            return ResultadoOperacao(
                sucesso=True,
                mensagem=(
                    f"Consolidação de {self.matricula} em '{self.componente}' "
                    f"(polo: {self.polo} | período: {self.periodo} | conceito: {conceito.upper()}) {acao}."
                ),
            )
        except Exception as exc:
            return ResultadoOperacao(
                sucesso=False,
                mensagem=f"Erro na consolidação: {exc}",
                detalhes=[repr(exc)],
            )

    # ── Versões síncronas (utilitários / testes) ──────────────────────────────

    def matricular_sync(self) -> ResultadoOperacao:
        """
        Versão síncrona de matricular().
        Útil para testes diretos fora de contexto async.
        NÃO use em callbacks do Streamlit — prefira a versão async.
        """
        return asyncio.run(self.matricular())

    def consolidar_sync(self, conceito: str = "E") -> ResultadoOperacao:
        """
        Versão síncrona de consolidar().
        Útil para testes diretos fora de contexto async.
        NÃO use em callbacks do Streamlit — prefira a versão async.
        """
        return asyncio.run(self.consolidar(conceito))
