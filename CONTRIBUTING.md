# Contribuindo

Crie uma branch curta, mantenha mudanças focadas e execute `pytest` antes de abrir uma revisão. JavaScript deve permanecer ES2020 sem dependências CDN; Python deve usar `snake_case`, type hints e logging. Migrations SQL são sequenciais e nunca devem reescrever migrations já publicadas.

Não envie `.env`, chaves do Supabase, dados pessoais ou arquivos brutos reais. Toda alteração de entidade publicada deve preservar a versão anterior e registrar o motivo.
