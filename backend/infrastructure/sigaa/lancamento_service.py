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
    componente : str  — Sigla do componente: ACC, ACC I, ACC II, ACC III, ACC IV, TCC, TCC I, TCC II
                        Se "ACC" → expande para [ACC I, ACC II, ACC III, ACC IV]
                        Se "TCC" → expande para [TCC I, TCC II]
    executar   : bool — Se False, faz dry-run (navega, preenche, mas NÃO confirma).
                        Padrão True (executa de fato).

    Raises
    ------
    ValueError — se o componente informado não for válido.
    """

    COMPONENTES_VALIDOS = {"ACC", "ACC I", "ACC II", "ACC III", "ACC IV", "TCC", "TCC I", "TCC II"}
    COMPONENTES_EXPANDIDOS = {
        "ACC": ["ACC I", "ACC II", "ACC III", "ACC IV"],
        "TCC": ["TCC I", "TCC II"],
    }

    def __init__(
        self,
        matricula: str,
        polo: str,
        periodo: str,
        componente: str,
        orientador: str | None = None,
        executar: bool = True,
    ) -> None:
        import logging
        logger = logging.getLogger(__name__)

        componente_upper = componente.strip().upper()
        logger.info(f"[LANCAMENTO_SERVICE] Validando componente: '{componente}' → '{componente_upper}'")

        if componente_upper not in self.COMPONENTES_VALIDOS:
            validos = ", ".join(sorted(self.COMPONENTES_VALIDOS))
            logger.error(f"[LANCAMENTO_SERVICE] Componente inválido: '{componente}'")
            raise ValueError(
                f"Componente inválido: '{componente}'. "
                f"Componentes válidos: {validos}"
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

    def _expand_componentes(self) -> list[str]:
        """Expande componente genérico (ACC, TCC) para lista específica."""
        if self.componente in self.COMPONENTES_EXPANDIDOS:
            return self.COMPONENTES_EXPANDIDOS[self.componente]
        return [self.componente]

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

        Se componente='ACC', matricula em ACC I, ACC II, ACC III, ACC IV.
        Se componente='TCC', matricula em TCC I, TCC II.
        Caso contrário, matricula no componente específico.

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
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"[MATRICULAR_SERVICE] Iniciando matricular para {self.matricula} | componente: {self.componente}")

        try:
            logger.info(f"[MATRICULAR_SERVICE] Importando executar_fluxo_direto...")
            from backend.infrastructure.sigaa.matricular import executar_fluxo_direto
            logger.info(f"[MATRICULAR_SERVICE] executar_fluxo_direto importado com sucesso")
        except ModuleNotFoundError as exc:
            logger.error(f"[MATRICULAR_SERVICE] Erro ao importar: {exc}")
            raise RuntimeError("Não foi possível importar o serviço de matrícula do SIGAA.") from exc

        componentes = self._expand_componentes()
        logger.info(f"[MATRICULAR_SERVICE] Componentes a matricular: {componentes}")

        erros = []
        matriculados = []

        for componente_spec in componentes:
            try:
                logger.info(f"[MATRICULAR_SERVICE] Processando: {componente_spec}")
                args = self._args_matricular()
                args.componente = componente_spec

                logger.info(f"[MATRICULAR_SERVICE] Chamando executar_fluxo_direto para {componente_spec}...")
                await executar_fluxo_direto(args)
                matriculados.append(componente_spec)
                logger.info(f"[MATRICULAR_SERVICE] ✓ {componente_spec} matriculado com sucesso")
            except Exception as exc:
                logger.exception(f"[MATRICULAR_SERVICE] ✗ Erro ao matricular {componente_spec}: {type(exc).__name__}: {str(exc)}")
                erros.append(f"{componente_spec}: {exc}")

        if matriculados:
            acao = "simulada (dry-run)" if not self.executar else "concluída com sucesso"
            mensagem = f"Matrícula de {self.matricula} em {', '.join(matriculados)} (polo: {self.polo} | período: {self.periodo}) {acao}."
            if erros:
                mensagem += f"\n⚠️ Componentes com erro: {'; '.join(erros)}"
            logger.info(f"[MATRICULAR_SERVICE] Resultado parcial: {len(matriculados)} de {len(componentes)}")
            return ResultadoOperacao(
                sucesso=True,
                mensagem=mensagem,
                detalhes=erros,
            )
        else:
            mensagem = f"Falha ao matricular todos os componentes: {'; '.join(erros)}"
            logger.error(f"[MATRICULAR_SERVICE] {mensagem}")
            return ResultadoOperacao(
                sucesso=False,
                mensagem=mensagem,
                detalhes=erros,
            )

    async def consolidar(self, conceito: str = "E") -> ResultadoOperacao:
        """
        Consolida a matrícula do aluno atribuindo o conceito informado.

        Se componente='ACC', consolida ACC I, ACC II, ACC III, ACC IV.
        Se componente='TCC', consolida TCC I, TCC II.
        Caso contrário, consolida o componente específico.

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
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"[CONSOLIDAR_SERVICE] Iniciando consolidação para {self.matricula} | componente: {self.componente} | conceito: {conceito}")

        try:
            if self.componente.startswith("TCC"):
                logger.info(f"[CONSOLIDAR_SERVICE] Importando consolidar_tcc...")
                from backend.infrastructure.sigaa.consolidar_tcc import executar_consolidacao
            else:
                logger.info(f"[CONSOLIDAR_SERVICE] Importando consolidar...")
                from backend.infrastructure.sigaa.consolidar import executar_consolidacao
        except ModuleNotFoundError as exc:
            logger.error(f"[CONSOLIDAR_SERVICE] Erro ao importar: {exc}")
            raise RuntimeError("Não foi possível importar o serviço de consolidação do SIGAA.") from exc

        componentes = self._expand_componentes()
        logger.info(f"[CONSOLIDAR_SERVICE] Componentes a consolidar: {componentes}")

        erros = []
        consolidados = []

        for componente_spec in componentes:
            try:
                logger.info(f"[CONSOLIDAR_SERVICE] Processando: {componente_spec}")
                args = self._args_consolidar(conceito)
                args.componente = componente_spec

                logger.info(f"[CONSOLIDAR_SERVICE] Chamando executar_consolidacao para {componente_spec}...")
                await executar_consolidacao(args)
                consolidados.append(componente_spec)
                logger.info(f"[CONSOLIDAR_SERVICE] ✓ {componente_spec} consolidado com sucesso")
            except Exception as exc:
                logger.exception(f"[CONSOLIDAR_SERVICE] ✗ Erro ao consolidar {componente_spec}: {type(exc).__name__}: {str(exc)}")
                erros.append(f"{componente_spec}: {exc}")

        if consolidados:
            acao = "simulada (dry-run)" if not self.executar else "concluída com sucesso"
            mensagem = f"Consolidação de {self.matricula} em {', '.join(consolidados)} (polo: {self.polo} | período: {self.periodo} | conceito: {conceito.upper()}) {acao}."
            if erros:
                mensagem += f"\n⚠️ Componentes com erro: {'; '.join(erros)}"
            logger.info(f"[CONSOLIDAR_SERVICE] Resultado parcial: {len(consolidados)} de {len(componentes)}")
            return ResultadoOperacao(
                sucesso=True,
                mensagem=mensagem,
                detalhes=erros,
            )
        else:
            mensagem = f"Falha ao consolidar todos os componentes: {'; '.join(erros)}"
            logger.error(f"[CONSOLIDAR_SERVICE] {mensagem}")
            return ResultadoOperacao(
                sucesso=False,
                mensagem=mensagem,
                detalhes=erros,
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
