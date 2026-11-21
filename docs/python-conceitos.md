- Permite definir a estrutura e tipo da chave de um dicionario, editor não permite usar nomes ou typos errados, logo evita problemas EXP
  from typing import Literal, NotRequired, TypedDict

- Literal serve apenas para o editar e verificador de tipo declarar se voce escreveu errado (não é enum). EXP
  Intent = Literal["knowledge", "productivity", "review", "planning"]
