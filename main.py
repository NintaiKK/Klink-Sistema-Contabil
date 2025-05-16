import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import ofxparse
from xml.etree import ElementTree as ET
from xml.dom import minidom
from fpdf import FPDF
import os
from datetime import datetime
from tkcalendar import DateEntry

class FinanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Balanço Financeiro")
        self.root.geometry("900x600")
        
        self.clientes = {
            # Estrutura correta:
            # 'cliente_id': {
            #     'nome': 'Nome',
            #     'contas': {
            #         'conta_id': {
            #             'banco': 'Banco',
            #             'numero': '123',
            #             'transactions': [],  # Agora as transações estão dentro de cada conta
            #             'periodos': {'inicio': None, 'fim': None}
            #         }
            #     },
            #     'balance_data': {  # Dados consolidados
            #         'receitas': 0,
            #         'despesas': 0,
            #         'saldo': 0,
            #         'categorias': {}
            #     }
            # }
        }
        self.cliente_atual = None
        self.conta_atual = None
    
    # Criar notebook (abas)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True)

    # Criar as abas
        self.create_client_tab()
        self.create_account_tab()
        self.create_import_tab()
        self.create_view_tab()
        self.create_balance_tab()

        self.status_conta_label = ttk.Label(self.root, text="Conta selecionada: Nenhuma")
        self.status_conta_label.pack(side='bottom', fill='x')

    def create_client_tab(self):
        """Cria a aba de gerenciamento de clientes"""
        client_tab = ttk.Frame(self.notebook)
        self.notebook.add(client_tab, text="Clientes")

        # Frame de cadastro
        register_frame = ttk.LabelFrame(client_tab, text="Cadastrar Novo Cliente")
        register_frame.pack(pady=10, padx=10, fill='x')

        ttk.Label(register_frame, text="Nome do Cliente:").grid(row=0, column=0, padx=5, pady=5)
        self.nome_cliente_entry = ttk.Entry(register_frame, width=40)
        self.nome_cliente_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(register_frame, text="Adicionar Cliente",
                  command=self.adicionar_cliente).grid(row=0, column=2, padx=5, pady=5)

        # Lista de clientes
        list_frame = ttk.LabelFrame(client_tab, text="Clientes Cadastrados")
        list_frame.pack(pady=10, padx=10, fill='both', expand=True)

        # Treeview para clientes
        columns = ('id', 'nome', 'transacoes', 'saldo')
        self.client_tree = ttk.Treeview(list_frame, columns=columns, show='headings')

        # Definir cabeçalhos
        self.client_tree.heading('id', text='ID')
        self.client_tree.heading('nome', text='Nome')
        self.client_tree.heading('transacoes', text='Transações')
        self.client_tree.heading('saldo', text='Saldo')

        # Definir largura das colunas
        self.client_tree.column('id', width=50)
        self.client_tree.column('nome', width=200)
        self.client_tree.column('transacoes', width=100)
        self.client_tree.column('saldo', width=100)

        self.client_tree.pack(fill='both', expand=True, padx=10, pady=10)

        # Botões de ação
        button_frame = ttk.Frame(list_frame)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Selecionar Cliente",
                  command=self.selecionar_cliente).pack(side='left', padx=5)

        ttk.Button(button_frame, text="Remover Cliente",
                  command=self.remover_cliente).pack(side='left', padx=5)

        # Atualizar lista de clientes
        self.update_client_list()

    def adicionar_cliente(self):
        """Adiciona um novo cliente com a estrutura correta"""
        nome = self.nome_cliente_entry.get().strip()
        if not nome:
            messagebox.showwarning("Aviso", "Digite um nome para o cliente")
            return

        cliente_id = str(len(self.clientes) + 1)
        self.clientes[cliente_id] = {
            'nome': nome,
            'contas': {},  # Contas serão adicionadas posteriormente
            'balance_data': {
                'receitas': 0,
                'despesas': 0,
                'saldo': 0,
                'categorias': {}
            }
        }

        self.nome_cliente_entry.delete(0, 'end')
        self.update_client_list()
        messagebox.showinfo("Sucesso", f"Cliente {nome} adicionado com ID {cliente_id}")

    def selecionar_cliente(self):
        """Seleciona cliente com verificação robusta"""
        try:
            selected = self.client_tree.selection()
            if not selected:
                raise ValueError("Nenhum cliente selecionado")
            
            item = self.client_tree.item(selected[0])
            cliente_id = str(item['values'][0])  # Garante que é string
            
            if cliente_id not in self.clientes:
                raise KeyError(f"Cliente ID {cliente_id} não encontrado")
            
            self.cliente_atual = cliente_id
            cliente = self.clientes[cliente_id]
            
            # Atualiza interface
            self.root.title(f"Sistema Financeiro - {cliente['nome']}")
            self.update_transaction_view()
            self.update_balance_view()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao selecionar cliente: {str(e)}")

    def remover_cliente(self):
        """Remove um cliente do sistema"""
        selected = self.client_tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione um cliente para remover")
            return

        item = self.client_tree.item(selected[0])
        cliente_id = item['values'][0]
        cliente_nome = self.clientes[cliente_id]['nome']

        if messagebox.askyesno("Confirmar", f"Remover o cliente {cliente_nome}? Todos os dados serão perdidos."):
            del self.clientes[cliente_id]

                # Se o cliente removido era o atual, limpar seleção
            if self.cliente_atual == cliente_id:
                self.cliente_atual = None
                self.root.title("Sistema de Balanço Financeiro")

            self.update_client_list()
            messagebox.showinfo("Sucesso", f"Cliente {cliente_nome} removido")

    def verificar_consistencia(self):
        """Verifica a consistência dos dados dos clientes"""
        for cliente_id in list(self.clientes.keys()):
            if not isinstance(cliente_id, str):
                print(f"Aviso: ID {cliente_id} não é string")
            if 'nome' not in self.clientes[cliente_id]:
                print(f"Aviso: Cliente {cliente_id} não tem nome definido")

    def update_client_list(self):
        """Atualiza a lista de clientes mostrando o total de transações de todas as contas"""
        for item in self.client_tree.get_children():
            self.client_tree.delete(item)

        for cliente_id, dados in self.clientes.items():
            # Calcula o total de transações de todas as contas do cliente
            total_transacoes = 0
            if 'contas' in dados:
                for conta in dados['contas'].values():
                    total_transacoes += len(conta['transactions'])

            saldo = dados['balance_data']['saldo']
            saldo_str = f"R$ {saldo:,.2f}"

            self.client_tree.insert('', 'end', values=(
                cliente_id,
                dados['nome'],
                total_transacoes,
                saldo_str
            ))

    def create_account_tab(self):
        """Cria aba para gerenciar contas bancárias"""
        account_tab = ttk.Frame(self.notebook)
        self.notebook.add(account_tab, text="Contas Bancárias")

        # Frame para adicionar novas contas
        add_frame = ttk.LabelFrame(account_tab, text="Adicionar Conta")
        add_frame.pack(pady=10, padx=10, fill='x')

        ttk.Label(add_frame, text="Banco:").grid(row=0, column=0, padx=5, pady=5)
        self.banco_entry = ttk.Entry(add_frame)
        self.banco_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(add_frame, text="Número:").grid(row=1, column=0, padx=5, pady=5)
        self.numero_conta_entry = ttk.Entry(add_frame)
        self.numero_conta_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(add_frame, text="Adicionar Conta", 
                  command=self.adicionar_conta).grid(row=2, column=1, pady=10)

        # Treeview para listar contas
        self.account_tree = ttk.Treeview(account_tab, columns=('id', 'banco', 'numero', 'periodo', 'transacoes'), show='headings')
        self.account_tree.heading('id', text='ID')
        self.account_tree.heading('banco', text='Banco')
        self.account_tree.heading('numero', text='Número')
        self.account_tree.heading('periodo', text='Período')
        self.account_tree.heading('transacoes', text='Transações')
        self.account_tree.pack(fill='both', expand=True, padx=10, pady=10)

            # Adicione um frame para os botões
        button_frame = ttk.Frame(account_tab)
        button_frame.pack(pady=10)

        # Botão para selecionar conta
        ttk.Button(button_frame, text="Selecionar Conta",
                  command=self.selecionar_conta).pack(side='left', padx=5)
        
        # Botão para remover conta (opcional)
        ttk.Button(button_frame, text="Remover Conta",
                  command=self.remover_conta).pack(side='left', padx=5)

        self.account_tree.pack(fill='both', expand=True, padx=10, pady=10)

    def adicionar_conta(self):
        """Adiciona uma nova conta ao cliente atual"""
        if not self.cliente_atual:
            messagebox.showwarning("Aviso", "Selecione um cliente primeiro")
            return

        # Garante que a estrutura 'contas' existe
        if 'contas' not in self.clientes[self.cliente_atual]:
            self.clientes[self.cliente_atual]['contas'] = {}

        banco = self.banco_entry.get().strip()
        numero = self.numero_conta_entry.get().strip()

        if not banco or not numero:
            messagebox.showwarning("Aviso", "Preencha todos os campos da conta")
            return

        # Gera ID da conta (pode ser sequencial ou usar UUID)
        contas = self.clientes[self.cliente_atual]['contas']
        conta_id = str(len(contas) + 1)

        contas[conta_id] = {
            'banco': banco,
            'numero': numero,
            'transactions': [],
            'periodos': {
                'inicio': None,
                'fim': None
            }
        }

        # Limpa os campos e atualiza a interface
        self.banco_entry.delete(0, 'end')
        self.numero_conta_entry.delete(0, 'end')
        self.update_account_list()
        messagebox.showinfo("Sucesso", f"Conta {banco} - {numero} adicionada")

    def remover_conta(self):
        """Remove a conta selecionada"""
        if not self.cliente_atual:
            messagebox.showwarning("Aviso", "Selecione um cliente primeiro")
            return

        selected = self.account_tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione uma conta para remover")
            return

        item = self.account_tree.item(selected[0])
        conta_id = item['values'][0]

        conta = self.clientes[self.cliente_atual]['contas'][conta_id]
        if messagebox.askyesno("Confirmar", f"Remover conta {conta['banco']} - {conta['numero']}?"):
            del self.clientes[self.cliente_atual]['contas'][conta_id]
            
            # Se estava selecionada, deseleciona
            if self.conta_atual == conta_id:
                self.conta_atual = None
            
            self.update_account_list()
            self.calcular_balanco()
            messagebox.showinfo("Sucesso", "Conta removida")

    def update_account_list(self):
        """Atualiza a lista de contas com verificação de estrutura"""
        # Limpa a treeview
        for item in self.account_tree.get_children():
            self.account_tree.delete(item)

        if not self.cliente_atual:
            return

        # Verifica e corrige a estrutura
        self.verificar_contas_cliente(self.cliente_atual)

        # Adiciona as contas à treeview
        for conta_id, conta in self.clientes[self.cliente_atual]['contas'].items():
            periodo = "Período não definido"
            if conta['periodos']['inicio'] and conta['periodos']['fim']:
                periodo = f"{conta['periodos']['inicio'].strftime('%d/%m/%Y')} - {conta['periodos']['fim'].strftime('%d/%m/%Y')}"

            self.account_tree.insert('', 'end', 
                values=(
                    conta_id,
                    conta['banco'],
                    conta['numero'],
                    periodo,
                    len(conta['transactions'])
                ),
                tags=('selected' if conta_id == self.conta_atual else '')
            )

        # Aplica formatação para a conta selecionada
        self.account_tree.tag_configure('selected', background='#e0e0ff')

    def selecionar_conta(self):
        """Seleciona uma conta com verificações robustas"""
        try:
            # Verifica se há um cliente selecionado
            if not self.cliente_atual:
                messagebox.showwarning("Aviso", "Selecione um cliente antes de escolher uma conta")
                return

            # Verifica se há itens selecionados na treeview
            selected = self.account_tree.selection()
            if not selected:
                messagebox.showwarning("Aviso", "Selecione uma conta na lista")
                return

            # Obtém os dados da conta selecionada
            item = self.account_tree.item(selected[0])
            if not item or 'values' not in item or len(item['values']) < 1:
                messagebox.showerror("Erro", "Dados da conta inválidos")
                return

            conta_id = str(item['values'][0])  # Garante que é string

            # Verifica se o cliente tem contas
            if 'contas' not in self.clientes[self.cliente_atual]:
                messagebox.showerror("Erro", "Nenhuma conta cadastrada para este cliente")
                return

            # Verifica se a conta existe
            if conta_id not in self.clientes[self.cliente_atual]['contas']:
                messagebox.showerror("Erro", 
                    f"Conta ID {conta_id} não encontrada\n"
                    f"Contas disponíveis: {list(self.clientes[self.cliente_atual]['contas'].keys())}")
                return

            # Define a conta atual e atualiza a interface
            self.conta_atual = conta_id
            conta = self.clientes[self.cliente_atual]['contas'][conta_id]
            self.status_conta_label.config(text=f"Conta selecionada: {conta['banco']} ({conta['numero']})")
            
            # Atualiza as visualizações
            self.update_transaction_view()
            messagebox.showinfo("Sucesso", f"Conta {conta['banco']} selecionada")

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao selecionar conta: {str(e)}")

    def verificar_contas_cliente(self, cliente_id):
        """Verifica e corrige a estrutura de contas de um cliente"""
        if cliente_id not in self.clientes:
            return False
        
        if 'contas' not in self.clientes[cliente_id]:
            self.clientes[cliente_id]['contas'] = {}
        
        return True

    def create_import_tab(self):
        """Cria a aba de importação de arquivos OFX"""
        import_tab = ttk.Frame(self.notebook)
        self.notebook.add(import_tab, text="Importar OFX")

        # Frame de instruções
        instruction_frame = ttk.LabelFrame(import_tab, text="Instruções")
        instruction_frame.pack(pady=10, padx=10, fill='x')

        ttk.Label(instruction_frame,
                 text="Selecione um arquivo OFX para importar os dados bancários").pack(pady=5)

        # Frame de botões
        button_frame = ttk.Frame(import_tab)
        button_frame.pack(pady=20)

        ttk.Button(button_frame, text="Selecionar Arquivo OFX",
                  command=self.import_ofx).pack(side='left', padx=5)

        ttk.Button(button_frame, text="Salvar em XML",
                  command=self.save_to_xml).pack(side='left', padx=5)

        # Área de status
        self.status_label = ttk.Label(import_tab, text="Pronto para importar")
        self.status_label.pack(pady=10)

    def create_view_tab(self):
        """Cria a aba de visualização de transações"""
        view_tab = ttk.Frame(self.notebook)
        self.notebook.add(view_tab, text="Visualizar Transações")

        # Treeview para mostrar transações
        columns = ('date', 'memo', 'amount', 'type', 'category')
        self.transaction_tree = ttk.Treeview(view_tab, columns=columns, show='headings')

        # Definir cabeçalhos
        self.transaction_tree.heading('date', text='Data')
        self.transaction_tree.heading('memo', text='Descrição')
        self.transaction_tree.heading('amount', text='Valor')
        self.transaction_tree.heading('type', text='Tipo')
        self.transaction_tree.heading('category', text='Categoria')

        # Definir largura das colunas
        self.transaction_tree.column('date', width=100)
        self.transaction_tree.column('memo', width=250)
        self.transaction_tree.column('amount', width=100)
        self.transaction_tree.column('type', width=100)
        self.transaction_tree.column('category', width=150)

        self.transaction_tree.pack(fill='both', expand=True, padx=10, pady=10)

        # Frame de botões
        button_frame = ttk.Frame(view_tab)
        button_frame.pack(pady=10)

        ttk.Button(button_frame, text="Atualizar Visualização",
                  command=self.update_transaction_view).pack(side='left', padx=5)

        ttk.Button(button_frame, text="Abrir Visualização Detalhada",
                  command=self.open_detailed_view).pack(side='left', padx=5)

    def create_balance_tab(self):
        """Cria a aba de balanço financeiro"""
        balance_tab = ttk.Frame(self.notebook)
        self.notebook.add(balance_tab, text="Balanço Financeiro")

        # Frame de resumo
        summary_frame = ttk.LabelFrame(balance_tab, text="Resumo Financeiro")
        summary_frame.pack(pady=10, padx=10, fill='x')

        # Labels de resumo
        ttk.Label(summary_frame, text="Receitas:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        self.income_label = ttk.Label(summary_frame, text="R$ 0,00", foreground='green')
        self.income_label.grid(row=0, column=1, sticky='w', padx=5, pady=5)

        ttk.Label(summary_frame, text="Despesas:").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        self.expense_label = ttk.Label(summary_frame, text="R$ 0,00", foreground='red')
        self.expense_label.grid(row=1, column=1, sticky='w', padx=5, pady=5)

        ttk.Label(summary_frame, text="Saldo:").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        self.balance_label = ttk.Label(summary_frame, text="R$ 0,00", foreground='blue')
        self.balance_label.grid(row=2, column=1, sticky='w', padx=5, pady=5)

        # Frame de categorias
        category_frame = ttk.LabelFrame(balance_tab, text="Por Categoria")
        category_frame.pack(pady=10, padx=10, fill='both', expand=True)

        # Treeview para categorias
        columns = ('category', 'amount')
        self.category_tree = ttk.Treeview(category_frame, columns=columns, show='headings')

        self.category_tree.heading('category', text='Categoria')
        self.category_tree.heading('amount', text='Valor')

        self.category_tree.column('category', width=200)
        self.category_tree.column('amount', width=150)

        self.category_tree.pack(fill='both', expand=True, padx=10, pady=10)

        # Botão para gerar PDF
        ttk.Button(balance_tab, text="Gerar Relatório em PDF",
                  command=self.generate_pdf).pack(pady=10)

    def import_ofx(self):
        if not self.verificar_conta_selecionada():
            return
        
        if not self.cliente_atual or not self.conta_atual:
            messagebox.showwarning("Aviso", "Selecione um cliente e uma conta")
            return
        if not self.conta_atual:
            messagebox.showwarning("Aviso", "Selecione uma conta primeiro")
            return

        filepath = filedialog.askopenfilename(filetypes=(("OFX files", "*.ofx"), ("All files", "*.*")))
        if not filepath:
            return

        try:
            with open(filepath, 'rb') as file:
                ofx = ofxparse.OfxParser.parse(file)

            conta = self.clientes[self.cliente_atual]['contas'][self.conta_atual]
            transactions = []

            for t in ofx.account.statement.transactions:
                trans_data = {
                    'date': t.date,
                    'amount': float(t.amount),
                    'type': 'CREDIT' if float(t.amount) > 0 else 'DEBIT',
                    'memo': t.memo,
                    'category': 'Não categorizado'
                }
                transactions.append(trans_data)

            conta['transactions'].extend(transactions)
            
            # Atualiza período
            if not conta['periodos']['inicio']:
                conta['periodos']['inicio'] = min(t['date'] for t in transactions)
            conta['periodos']['fim'] = max(t['date'] for t in transactions)

            self.calcular_balanco()
            self.update_account_list()
            messagebox.showinfo("Sucesso", f"Importadas {len(transactions)} transações")

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao importar: {str(e)}")

    def verificar_conta_selecionada(self):
        """Verifica se há uma conta válida selecionada"""
        if not self.cliente_atual:
            messagebox.showwarning("Aviso", "Nenhum cliente selecionado")
            return False
        
        if not self.conta_atual:
            messagebox.showwarning("Aviso", "Nenhuma conta selecionada")
            return False
        
        if not self.verificar_contas_cliente(self.cliente_atual):
            messagebox.showerror("Erro", "Estrutura de contas inválida")
            return False
        
        if self.conta_atual not in self.clientes[self.cliente_atual]['contas']:
            messagebox.showerror("Erro", "A conta selecionada não existe mais")
            self.conta_atual = None
            return False
        
        return True

    def save_to_xml(self):
        """Salva os dados do cliente atual em XML"""
        if not self.cliente_atual:
            messagebox.showwarning("Aviso", "Selecione um cliente primeiro")
            return

        cliente = self.clientes[self.cliente_atual]
        balance_data = cliente['balance_data']
        transactions = cliente['transactions']

        try:
            # Criar estrutura XML
            root = ET.Element('financeiro')
            ET.SubElement(root, 'cliente_id').text = self.cliente_atual
            ET.SubElement(root, 'cliente_nome').text = cliente['nome']

            # Adicionar balanço
            balance = ET.SubElement(root, 'balanco')
            ET.SubElement(balance, 'receitas').text = str(balance_data['receitas'])
            ET.SubElement(balance, 'despesas').text = str(balance_data['despesas'])
            ET.SubElement(balance, 'saldo').text = str(balance_data['saldo'])

            # Adicionar categorias
            categories = ET.SubElement(root, 'categorias')
            for cat, amount in balance_data['categorias'].items():
                category = ET.SubElement(categories, 'categoria')
                ET.SubElement(category, 'nome').text = cat
                ET.SubElement(category, 'valor').text = str(amount)

            # Adicionar transações
            transactions_xml = ET.SubElement(root, 'transacoes')
            for trans in transactions:
                transaction = ET.SubElement(transactions_xml, 'transacao')
                ET.SubElement(transaction, 'data').text = trans['date'].strftime('%Y-%m-%d')
                ET.SubElement(transaction, 'descricao').text = trans['memo']
                ET.SubElement(transaction, 'valor').text = str(trans['amount'])
                ET.SubElement(transaction, 'tipo').text = trans['type']
                ET.SubElement(transaction, 'categoria').text = trans['category']

            # Formatar XML
            xml_str = ET.tostring(root, encoding='unicode')
            dom = minidom.parseString(xml_str)
            pretty_xml = dom.toprettyxml(indent="  ")

            # Salvar arquivo
            filepath = filedialog.asksaveasfilename(
                defaultextension=".xml",
                filetypes=(("XML files", "*.xml"), ("All files", "*.*")),
                title="Salvar como XML"
            )

            if filepath:
                with open(filepath, 'w', encoding='utf-8') as file:
                    file.write(pretty_xml)

                self.status_label.config(text=f"Dados salvos em {filepath}")
                messagebox.showinfo("Sucesso", f"Dados do cliente {cliente['nome']} salvos com sucesso")

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar XML: {str(e)}")

    def update_account_list(self):
        """Atualiza a lista de contas na interface"""
        if not self.cliente_atual:
            return

        # Limpa a treeview
        for item in self.account_tree.get_children():
            self.account_tree.delete(item)

        # Adiciona as contas do cliente atual
        if 'contas' in self.clientes[self.cliente_atual]:
            for conta_id, conta in self.clientes[self.cliente_atual]['contas'].items():
                periodo = ""
                if conta['periodos']['inicio']:
                    periodo = f"{conta['periodos']['inicio'].strftime('%d/%m/%Y')} a {conta['periodos']['fim'].strftime('%d/%m/%Y')}"

                self.account_tree.insert('', 'end', values=(
                    conta_id,
                    conta['banco'],
                    conta['numero'],
                    periodo,
                    len(conta['transactions'])
                ))

    def update_transaction_view(self):
        """Mostra todas as transações do cliente atual, de todas as contas"""
        for item in self.transaction_tree.get_children():
            self.transaction_tree.delete(item)

        if not self.cliente_atual or 'contas' not in self.clientes[self.cliente_atual]:
            return

        for conta_id, conta in self.clientes[self.cliente_atual]['contas'].items():
            for trans in conta['transactions']:
                amount = trans['amount']
                amount_str = f"R$ {abs(amount):,.2f}"
                
                self.transaction_tree.insert('', 'end', values=(
                    trans['date'].strftime('%d/%m/%Y'),
                    f"{conta['banco']} - {trans['memo']}",
                    amount_str,
                    trans['type'],
                    trans['category']
                ))

    def calcular_balanco(self):
        """Calcula o balanço consolidado de todas as contas do cliente atual"""
        if not self.cliente_atual:
            return

        cliente = self.clientes[self.cliente_atual]
        saldo_total = {
            'receitas': 0,
            'despesas': 0,
            'saldo': 0,
            'categorias': {}
        }

        # Zera os valores antes de recalcular
        cliente['balance_data'] = saldo_total.copy()

        if 'contas' not in cliente:
            cliente['contas'] = {}

        for conta in cliente['contas'].values():
            for trans in conta['transactions']:
                valor = trans['amount']
                if valor > 0:
                    saldo_total['receitas'] += valor
                else:
                    saldo_total['despesas'] += abs(valor)
                
                saldo_total['saldo'] += valor
                
                categoria = trans['category']
                if categoria not in saldo_total['categorias']:
                    saldo_total['categorias'][categoria] = 0
                saldo_total['categorias'][categoria] += valor

        cliente['balance_data'] = saldo_total
        self.update_balance_view()

    def update_balance_view(self):
        """Atualiza a visualização do balanço do cliente atual"""
        if not self.cliente_atual:
            self.income_label.config(text="R$ 0,00")
            self.expense_label.config(text="R$ 0,00")
            self.balance_label.config(text="R$ 0,00")

            for item in self.category_tree.get_children():
                self.category_tree.delete(item)
            return

        cliente = self.clientes[self.cliente_atual]
        balance_data = cliente['balance_data']

        self.income_label.config(text=f"R$ {balance_data['receitas']:,.2f}")
        self.expense_label.config(text=f"R$ {balance_data['despesas']:,.2f}")
        self.balance_label.config(text=f"R$ {balance_data['saldo']:,.2f}")

        # Atualizar categorias
        for item in self.category_tree.get_children():
            self.category_tree.delete(item)

        for cat, amount in balance_data['categorias'].items():
            amount_str = f"R$ {amount:,.2f}" if amount >= 0 else f"-R$ {abs(amount):,.2f}"
            self.category_tree.insert('', 'end', values=(cat, amount_str))

    def open_detailed_view(self):
        """Abre uma janela com a visualização detalhada da transação selecionada"""
        selected = self.transaction_tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione uma transação para visualizar")
            return

        item = self.transaction_tree.item(selected[0])
        values = item['values']

        # Janela de detalhes
        detail_window = tk.Toplevel(self.root)
        detail_window.title("Detalhes da Transação")
        detail_window.geometry("400x300")

        # Frame de detalhes
        detail_frame = ttk.LabelFrame(detail_window, text="Detalhes")
        detail_frame.pack(pady=10, padx=10, fill='both', expand=True)

        # Mostrar detalhes
        ttk.Label(detail_frame, text=f"Data: {values[0]}").pack(anchor='w', pady=5)
        ttk.Label(detail_frame, text=f"Descrição: {values[1]}").pack(anchor='w', pady=5)
        ttk.Label(detail_frame, text=f"Valor: {values[2]}").pack(anchor='w', pady=5)
        ttk.Label(detail_frame, text=f"Tipo: {values[3]}").pack(anchor='w', pady=5)
        ttk.Label(detail_frame, text=f"Categoria: {values[4]}").pack(anchor='w', pady=5)

        ttk.Button(detail_window, text="Fechar", command=detail_window.destroy).pack(pady=10)

    def create_filters(self):
        """Cria controles para filtros"""
        filter_frame = ttk.Frame(self.view_tab)  # Assumindo que view_tab é sua aba de visualização
        filter_frame.pack(fill='x', padx=10, pady=5)

        # Filtro por conta
        ttk.Label(filter_frame, text="Conta:").pack(side='left')
        self.conta_filter = ttk.Combobox(filter_frame, values=self.get_contas_list())
        self.conta_filter.pack(side='left', padx=5)
        self.conta_filter.bind('<<ComboboxSelected>>', self.apply_filters)

        # Filtro por período
        ttk.Label(filter_frame, text="De:").pack(side='left')
        self.date_from = DateEntry(filter_frame)
        self.date_from.pack(side='left', padx=5)

        ttk.Label(filter_frame, text="Até:").pack(side='left')
        self.date_to = DateEntry(filter_frame)
        self.date_to.pack(side='left', padx=5)

        ttk.Button(filter_frame, text="Aplicar", command=self.apply_filters).pack(side='left')

    def apply_filters(self, event=None):
        conta_id = self.conta_filter.get()
        date_from = self.date_from.get_date()
        date_to = self.date_to.get_date()

        # Implemente a lógica de filtro aqui
        # Atualize a visualização com as transações filtradas

    def generate_pdf(self):
        """Gera um relatório em PDF"""
        if not self.cliente_atual:
            messagebox.showwarning("Aviso", "Selecione um cliente primeiro")
            return

        cliente = self.clientes[self.cliente_atual]
        balance_data = cliente['balance_data']

        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)

            # Título
            pdf.cell(200, 10, txt="Relatório Financeiro", ln=1, align='C')
            pdf.ln(10)

            # Data do relatório
            pdf.cell(200, 10, txt=f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=1)
            pdf.ln(5)

            # Nome do cliente
            pdf.cell(200, 10, txt=f"Cliente: {cliente['nome']}", ln=1)
            pdf.ln(5)

            # Resumo
            pdf.set_font("Arial", 'B', size=12)
            pdf.cell(200, 10, txt="Resumo Financeiro", ln=1)
            pdf.set_font("Arial", size=12)

            pdf.cell(100, 10, txt="Receitas:", ln=0)
            pdf.cell(50, 10, txt=f"R$ {balance_data['receitas']:,.2f}", ln=1)

            pdf.cell(100, 10, txt="Despesas:", ln=0)
            pdf.cell(50, 10, txt=f"R$ {balance_data['despesas']:,.2f}", ln=1)

            pdf.cell(100, 10, txt="Saldo:", ln=0)
            pdf.cell(50, 10, txt=f"R$ {balance_data['saldo']:,.2f}", ln=1)
            pdf.ln(10)

            # Categorias
            pdf.set_font("Arial", 'B', size=12)
            pdf.cell(200, 10, txt="Por Categoria", ln=1)
            pdf.set_font("Arial", size=12)

            for cat, amount in balance_data['categorias'].items():
                amount_str = f"R$ {amount:,.2f}" if amount >= 0 else f"-R$ {abs(amount):,.2f}"
                pdf.cell(120, 10, txt=cat, ln=0)
                pdf.cell(50, 10, txt=amount_str, ln=1)

            # Salvar arquivo
            filepath = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=(("PDF files", "*.pdf"), ("All files", "*.*")),
                title="Salvar Relatório PDF"
            )

            if filepath:
                pdf.output(filepath)
                messagebox.showinfo("Sucesso", f"Relatório salvo em {filepath}")

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar PDF: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = FinanceApp(root)
    root.mainloop()
