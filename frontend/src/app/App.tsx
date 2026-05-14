import { Routes, Route } from 'react-router-dom'
import { Layout } from '@/shared/components/Layout'

// Páginas
import { HomePage } from '@/features/home/HomePage'
import { FormACC } from '@/features/form-acc/FormACC'
import { FormTCC } from '@/features/form-tcc/FormTCC'
import { FormEstagio } from '@/features/form-estagio/FormEstagio'
import { FormSocial } from '@/features/form-social/FormSocial'
import { FormRequerimentoTCC } from '@/features/form-requerimento-tcc/FormRequerimentoTCC'
import { FormEmissaoDocumentos } from '@/features/form-emissao-docs/FormEmissaoDocumentos'
import { FormPlanoEnsino } from '@/features/form-plano-ensino/FormPlanoEnsino'
import { FormProjetos } from '@/features/form-projetos/FormProjetos'
import { FormAvaliacao } from '@/features/form-avaliacao/FormAvaliacao'
import { FAQPage } from '@/features/faq/FAQPage'
import { GestorAlertas } from '@/features/gestor-alertas/GestorAlertas'
import { LancamentoConceitos } from '@/features/lancamento-conceitos/LancamentoConceitos'
import { ConsultaRequerimentoTCC } from '@/features/consulta-requerimento-tcc/ConsultaRequerimentoTCC'
import { ConsultaProjetos } from '@/features/consulta-projetos/ConsultaProjetos'
import { ConfiguracaoPage } from '@/features/configuracao/ConfiguracaoPage'
import { DocumentosPage } from '@/features/documentos/DocumentosPage'
import { CalendariosPage } from '@/features/calendarios/CalendariosPage'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<HomePage />} />

        {/* Formulários Discentes */}
        <Route path="acc" element={<FormACC />} />
        <Route path="tcc" element={<FormTCC />} />
        <Route path="estagio" element={<FormEstagio />} />
        <Route path="social" element={<FormSocial />} />
        <Route path="requerimento-tcc" element={<FormRequerimentoTCC />} />
        <Route path="emissao-documentos" element={<FormEmissaoDocumentos />} />

        {/* Formulários Docentes */}
        <Route path="plano-ensino" element={<FormPlanoEnsino />} />
        <Route path="projetos" element={<FormProjetos />} />
        <Route path="avaliacao-gestao" element={<FormAvaliacao />} />

        {/* Geral */}
        <Route path="faq" element={<FAQPage />} />
        <Route path="documentos" element={<DocumentosPage />} />
        <Route path="calendarios" element={<CalendariosPage />} />

        {/* Admin */}
        <Route path="admin/alertas" element={<GestorAlertas />} />
        <Route path="admin/lancamentos" element={<LancamentoConceitos />} />

        {/* Consultas */}
        <Route path="consulta/requerimento-tcc" element={<ConsultaRequerimentoTCC />} />
        <Route path="consulta/projetos" element={<ConsultaProjetos />} />

        {/* Configuração */}
        <Route path="configuracao" element={<ConfiguracaoPage />} />
      </Route>
    </Routes>
  )
}
