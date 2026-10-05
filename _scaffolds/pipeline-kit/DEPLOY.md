# Estágio C — colocar o 3b no ar (plataforma operador-assistida)

Objetivo: **cliente faz pedido, acompanha, revisa, aprova e BAIXA a entrega sozinho**;
a **produção continua com o operador** (você + Claude) usando o pipeline. O console já está
pronto, multi-tenant (contas + dono) e com download das entregas aprovadas.

```
[cliente no navegador] --HTTPS--> [console Mesa de Corte] <--> orders/*.json + output/ (entregas)
                                         ^
                                         |  (mesma máquina, no modo simples)
                                   [pipeline de render]  --publica finais-->  output/  (ou object storage)
                                   (operador: você + Claude)
```

## Topologia — escolha UMA
**Opção 1 (recomendada p/ começar): console na própria máquina de render + Cloudflare Tunnel.**
- O console roda onde você renderiza → sem sincronizar nada. O túnel dá HTTPS + domínio sem abrir porta no roteador. Custo de servidor: **zero**.
- Passos:
  1. `useradd.py` cria as contas (cliente = `user`, você = `admin`).
  2. Rodar o console com auth: `MESA_TOKEN=<forte> py apps/mesa-de-corte/server.py` (contas já exigem login; o token é senha-mestra admin).
  3. `cloudflared tunnel --url http://127.0.0.1:8756` (ou túnel nomeado com domínio fixo). O túnel cuida do TLS.
  4. Manter de pé: **nssm** (Windows) ou Agendador de Tarefas rodando o `py server.py` no boot.

**Opção 2 (mais robusta, mais ops): VPS separado p/ o console, render na sua máquina.**
- Console num VPS (~US$5-10/mês). Precisa **compartilhar `orders/` e as entregas** entre VPS e a máquina de render → use **object storage** (ver abaixo) como fonte comum, ou um sync. Só vale quando o volume justificar.

## Entregas (download) — hoje e amanhã
- **Hoje (local-first, já funciona):** `/api/download?lote&item&fmt` serve o formato **aprovado** como anexo (gated por dono; não-admin só baixa aprovado). Botão ⬇ na UI por formato aprovado.
- **Próximo (quando for pro VPS/escala):** trocar o disco local por **object storage** (Cloudflare R2 ou S3): o operador sobe os finais aprovados; `/api/download` redireciona p/ uma URL assinada. Isolar numa camada `storage` (hoje = local; depois = R2/S3) — **não construir antes de escolher o provider** (evita abstração especulativa). Custo R2/S3: centavos por GB.

## Fluxo do operador (3b)
1. Cliente (ou você) cria o pedido no console → evento `START` + `_signal.txt`.
2. Você + Claude produzem com o pipeline (`build_item.sh` etc.).
3. `dress`/`set_status` publicam os finais em `output/` → aparecem no console.
4. Cliente revisa, **pede ajuste por parte**, **aprova por formato**; o histórico registra as rodadas.
5. Cliente **baixa** o formato aprovado (⬇ / `/api/download`).

## Segurança (checklist antes de expor)
- [x] Contas por usuário (`useradd.py`) + dono por lote (feito).
- [x] `/api/download` só serve formato aprovado p/ não-admin (feito).
- [ ] **HTTPS** sempre (túnel Cloudflare ou `MESA_CERT`/`MESA_KEY`).
- [ ] `MESA_TOKEN` forte (senha-mestra) + nunca expor sem auth (`MESA_HOST=0.0.0.0` exige token).
- [ ] Backup periódico de `orders/` (é o "banco" hoje).
- [ ] Limitar tamanho de upload (roteiro/b-roll) e revisar as rotas de upload.
- [ ] Rotacionar credenciais (ElevenLabs etc.); nunca commitar chave.

## O que falta p/ 3b "completo" (priorizado)
1. ✅ Download das entregas (feito).
2. **Deploy**: Cloudflare Tunnel + nssm/boot + domínio (ops, sem código novo).
3. Notificar o cliente quando a entrega sai (e-mail/webhook) — opcional.
4. Object storage (só ao ir pro VPS/escala).

## Custos aproximados (Opção 1)
- Cloudflare Tunnel: **grátis**. Domínio: ~US$10/ano (ou subdomínio grátis do túnel).
- Sem VPS. Energia/banda da sua máquina. Storage: local (já pago).

> Resumo: o 3b está a **um passo de ops** — contas, dono, revisão granular, áudio e **download**
> já existem. Falta **hospedar** (túnel) e, quando escalar, **object storage**. Nada disso exige
> refazer o produto.
