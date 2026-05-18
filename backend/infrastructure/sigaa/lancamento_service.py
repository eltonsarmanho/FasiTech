"""
lancamento_service.py — Serviço de backend para matrícula e consolidação no SIGAA.

Usado pelo frontend Streamlit. Por padrão roda em modo headless (sem janela).

Exemplos de uso (contexto async):

    # ACC
    svc = LancamentoService(
        matricula="202285940020",
        polo="OEIRAS DO PARÁ",
        periodo="2026.1",
        componente="ACC I",
    )
    resultado = await svc.matricular()
    resultado = await svc.consolidar(conceito="E")

    # TCC
    svc = LancamentoService(
        matricula="202416040009",
        polo="CAMETÁ",
        periodo="2026.2",
        componente="TCC I",
        orientador="ELTON SARMANHO SIQUEIRA",
    )
    resultado = await svc.matricular()
    resultado = await svc.consolidar(conceito="E")

    # Debug com janela visível
    svc = LancamentoService(..., headless=False)
"""

import asyncio
from dataclasses import dataclass, field
from types import SimpleNamespace


# ── Resultado ─────────────────────────────────────────────────────────────────


@dataclass
class ResultadoOperacao:
    sucesso: bool
    mensagem: str
    detalhes: list[str] = field(default_factory=list)


# ── Serviço ───────────────────────────────────────────────────────────────────


class LancamentoService:
    """
    Automatiza matrícula e consolidação no SIGAA via Playwright.

    Parâmetros
    ----------
    matricula  : Matrícula do aluno (ex: "202285940020")
    polo       : Nome do polo (ex: "OEIRAS DO PARÁ")
    periodo    : Período acadêmico (ex: "2026.1")
    componente : ACC I · ACC II · ACC III · ACC IV · TCC I · TCC II
    orientador : Obrigatório apenas para TCC
    executar   : False → dry-run (navega mas não confirma). Padrão True.
    headless   : False → abre janela do browser (útil para depuração). Padrão True.
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
        headless: bool = True,
    ) -> None:
        componente_upper = componente.strip().upper()
        if componente_upper not in self.COMPONENTES_VALIDOS:
            validos = ", ".join(sorted(self.COMPONENTES_VALIDOS))
            raise ValueError(
                f"Componente inválido: '{componente}'. Use um de: {validos}"
            )
        if componente_upper.startswith("TCC") and not orientador:
            raise ValueError(
                f"O campo 'orientador' é obrigatório para '{componente_upper}'."
            )

        self.matricula = matricula.strip()
        self.polo = polo.strip()
        self.periodo = periodo.strip()
        self.componente = componente_upper
        self.orientador = orientador
        self.executar = executar
        self.headless = headless

    # ── Helpers internos ──────────────────────────────────────────────────────

    def _expand_componentes(self) -> list[str]:
        """Expande componente genérico (ACC, TCC) para lista específica."""
        if self.componente in self.COMPONENTES_EXPANDIDOS:
            return self.COMPONENTES_EXPANDIDOS[self.componente]
        return [self.componente]

    # ── Builders de argumento ─────────────────────────────────────────────────

    def _args_matricular(self) -> SimpleNamespace:
        """Namespace esperado por sigaa_Matricular.executar_fluxo_direto
           e sigaa_Matricular_TCC.executar_fluxo_direto."""
        return SimpleNamespace(
            matricula=self.matricula,
            polo=self.polo,
            periodo=self.periodo,
            componente=self.componente,
            curso=None,           # usa polo para localizar curso no dropdown
            atividade_nome=None,  # usa nome padrão do MAPA_COMPONENTE
            orientador=self.orientador,
            executar=self.executar,
            headless=self.headless,
            manter_aberto=False,
        )

    def _args_consolidar(self, conceito: str) -> SimpleNamespace:
        """Namespace esperado por sigaa_Consolidar.executar_consolidacao
           e sigga_Consolidar_TCC.executar_consolidacao."""
        return SimpleNamespace(
            matricula=self.matricula,
            polo=self.polo,
            periodo=self.periodo,
            componente=self.componente,
            conceito=conceito.strip().upper(),
            curso=None,
            orientador=self.orientador,
            executar=self.executar,
            headless=self.headless,
            manter_aberto=False,
        )

    # ── Operações principais ──────────────────────────────────────────────────

    async def matricular(self) -> ResultadoOperacao:
        """
        Matrícula do aluno no componente via SIGAA.

        Se componente='ACC', matricula em ACC I, ACC II, ACC III, ACC IV.
        Se componente='TCC', matricula em TCC I, TCC II.

        Fluxo (ACC):
          Login → Período → Portal Coord. Graduação → Curso/Polo →
          Atividades > Matricular → Buscar Discente →
          Tipo de Atividade → Buscar → Selecionar → Próximo Passo →
          Senha → Confirmar

        Fluxo (TCC):
          Mesmo fluxo, porém usa sigaa_Matricular_TCC. Etapa extra:
          Dados de Registro → Orientador (autocomplete) → Próximo Passo → Senha → Confirmar.
        """
        componentes = self._expand_componentes()
        erros = []
        matriculados = []

        for componente_spec in componentes:
            try:
                if componente_spec.startswith("TCC"):
                    from backend.infrastructure.sigaa.matricular_tcc import executar_fluxo_direto
                else:
                    from backend.infrastructure.sigaa.matricular import executar_fluxo_direto

                args = self._args_matricular()
                args.componente = componente_spec

                await executar_fluxo_direto(args)
                matriculados.append(componente_spec)
            except Exception as exc:
                erros.append(f"{componente_spec}: {exc}")

        if matriculados:
            acao = "simulada (dry-run)" if not self.executar else "concluída com sucesso"
            mensagem = f"Matrícula de {self.matricula} em {', '.join(matriculados)} (polo: {self.polo} | período: {self.periodo}) {acao}."
            if erros:
                mensagem += f"\n⚠️ Erros: {'; '.join(erros)}"
            return ResultadoOperacao(
                sucesso=True,
                mensagem=mensagem,
                detalhes=erros + [f"SUCESSO: {comp}" for comp in matriculados],
            )
        else:
            return ResultadoOperacao(
                sucesso=False,
                mensagem=f"Falha ao matricular: {'; '.join(erros)}",
                detalhes=erros,
            )

    async def consolidar(self, conceito: str = "E") -> ResultadoOperacao:
        """
        Consolida a matrícula atribuindo o conceito informado.

        Se componente='ACC', consolida ACC I, ACC II, ACC III, ACC IV.
        Se componente='TCC', consolida TCC I, TCC II.

        Fluxo (ACC e TCC):
          Login → Período → Portal Coord. Graduação → Curso/Polo →
          Atividades > Consolidar Matrículas → Localizar Discente →
          Selecionar Conceito → Próximo Passo → Senha → Confirmar

        Parâmetros
        ----------
        conceito : Conceito a atribuir. Opções válidas: B, E, I, R, S. Padrão "E".
        """
        conceito_upper = conceito.strip().upper()
        conceitos_validos = {"B", "E", "I", "R", "S"}
        if conceito_upper not in conceitos_validos:
            raise ValueError(
                f"Conceito inválido: '{conceito}'. Use um de: {', '.join(sorted(conceitos_validos))}"
            )

        componentes = self._expand_componentes()
        erros = []
        consolidados = []

        for componente_spec in componentes:
            try:
                if componente_spec.startswith("TCC"):
                    from backend.infrastructure.sigaa.consolidar_tcc import executar_consolidacao
                else:
                    from backend.infrastructure.sigaa.consolidar import executar_consolidacao

                args = self._args_consolidar(conceito_upper)
                args.componente = componente_spec

                await executar_consolidacao(args)
                consolidados.append(componente_spec)
            except Exception as exc:
                erros.append(f"{componente_spec}: {exc}")

        if consolidados:
            acao = "simulada (dry-run)" if not self.executar else "concluída com sucesso"
            mensagem = f"Consolidação de {self.matricula} em {', '.join(consolidados)} (polo: {self.polo} | período: {self.periodo} | conceito: {conceito_upper}) {acao}."
            if erros:
                mensagem += f"\n⚠️ Erros: {'; '.join(erros)}"
            return ResultadoOperacao(
                sucesso=True,
                mensagem=mensagem,
                detalhes=erros + [f"SUCESSO: {comp}" for comp in consolidados],
            )
        else:
            # Mesmo com erros, retornar sucesso parcial se expandiu
            # Porque pode ser que o componente já estava consolidado
            if len(componentes) > 1:
                mensagem = f"Nenhum componente consolidado (possível: já consolidados ou indisponíveis no SIGAA).\nComponentes tentados: {', '.join(componentes)}"
                return ResultadoOperacao(
                    sucesso=False,
                    mensagem=f"Falha ao consolidar: {'; '.join(erros)}",
                    detalhes=erros,
                )
            else:
                return ResultadoOperacao(
                    sucesso=False,
                    mensagem=f"Falha ao consolidar: {'; '.join(erros)}",
                    detalhes=erros,
                )

    # ── Versões síncronas ─────────────────────────────────────────────────────

    def matricular_sync(self) -> ResultadoOperacao:
        """Versão síncrona de matricular(). Não use dentro de callbacks Streamlit."""
        return asyncio.run(self.matricular())

    def consolidar_sync(self, conceito: str = "E") -> ResultadoOperacao:
        """Versão síncrona de consolidar(). Não use dentro de callbacks Streamlit."""
        return asyncio.run(self.consolidar(conceito))
