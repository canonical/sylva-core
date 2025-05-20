// tools/vscode-units-extension/extension.ts
import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'yaml';
import * as yamlAst from 'yaml-ast-parser';

let settingsMap: Record<string, any> = {};

let documentedDecoration: vscode.TextEditorDecorationType;

export function activate(context: vscode.ExtensionContext) {
  const rootPath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
  if (!rootPath) return;

  console.log(rootPath)

  const settingsPath = path.join(rootPath, 'schemas', 'units-settings.yaml');
  const valuesPath = path.join(rootPath, 'values.yaml');

  try {
    const rawYaml = fs.readFileSync(settingsPath, 'utf-8');
    settingsMap = yaml.parse(rawYaml);
  } catch (err) {
    console.error('Failed to load units-settings.yaml:', err);
    return;
  }

  createDecoration()

  // Hover provider
  context.subscriptions.push(
    vscode.languages.registerHoverProvider('yaml', {
      provideHover(document, position) {
        const line = document.lineAt(position.line).text;
        const match = line.match(/upstream_path:\s*(\.[\w.]+)/);
        if (match) {
          const pathStr = match[1];
          const info: any = findInfoByPath(pathStr);
          if (info) {
            return new vscode.Hover(
              `**${info.description || 'No description'}**\n\nExample: \`${info.example || '—'}\`\nInjected into: \`${info.upstream_path}\``
            );
          }
        }
        return null;
      },
    })
  );

  // Go to definition provider
  context.subscriptions.push(
    vscode.languages.registerDefinitionProvider('yaml', {
      async provideDefinition(document, position) {
        const line = document.lineAt(position.line).text;
        const match = line.match(/upstream_path:\s*(\.[\w.]+)/);
        if (!match) return;

        const valuesDocText = fs.readFileSync(valuesPath, 'utf-8');
        const valuesTextDocument = await vscode.workspace.openTextDocument(valuesPath); // ✅ actual doc for accurate positionAt
        const ast = yamlAst.load(valuesDocText) as yamlAst.YAMLNode;

        const pathStr = match[1].slice(1); // remove leading dot
        const keys = pathStr.split('.');

        console.log(pathStr)

        const targetNode = findNodeByPath(ast, keys);

        if (!targetNode) return;

        const startPos = valuesTextDocument.positionAt(targetNode.startPosition);
        return new vscode.Location(valuesTextDocument.uri, startPos);
      },
    })
  );

  const activeDoc = vscode.window.activeTextEditor?.document;
  if (activeDoc?.fileName.endsWith('values.yaml')) {
    decorateDocumentedKeys(activeDoc);
  }

  context.subscriptions.push(
    vscode.workspace.onDidOpenTextDocument((doc) => {
      if (doc.fileName.endsWith('values.yaml')) {
        decorateDocumentedKeys(doc);
      }
    })
  );

  context.subscriptions.push(
    vscode.workspace.onDidChangeTextDocument((e) => {
      if (e.document.fileName.endsWith('values.yaml')) {
        decorateDocumentedKeys(e.document);
      }
    })
  );

  context.subscriptions.push(
    vscode.window.onDidChangeActiveTextEditor((editor) => {
      if (editor?.document.fileName.includes('values.yaml')) {
        decorateDocumentedKeys(editor.document);
      }
    })
  );

}

async function decorateDocumentedKeys(doc: vscode.TextDocument) {
  const editor = vscode.window.visibleTextEditors.find(e => e.document.fileName === doc.fileName);
  if (!editor) return;

  const raw = doc.getText();
  const ast = yamlAst.load(raw);
  const decorations: vscode.DecorationOptions[] = [];

  for (const [unit, fields] of Object.entries(settingsMap)) {
    for (const [key, props] of Object.entries(fields)) {
      const upstream = (props as any)?.upstream_path;
      if (typeof upstream !== 'string') continue;

      const pathSegments = upstream.replace(/^\./, '').split('.');
      const targetNode = findNodeByPath(ast, pathSegments);
      if (!targetNode) {
        console.warn(`Could not find path in values.yaml:`, pathSegments.join('.'));
        continue
      }

      const line = doc.positionAt(targetNode.startPosition).line;
      const range = new vscode.Range(line, doc.lineAt(line).range.end.character, line, doc.lineAt(line).range.end.character);
      decorations.push({ range });
    }
  }

  editor.setDecorations(documentedDecoration, decorations);
}


function findNodeByPath(ast: yamlAst.YAMLNode, pathSegments: string[]): yamlAst.YAMLNode | null {
  let currentNode = ast;

  for (const segment of pathSegments) {
    if (currentNode.kind !== yamlAst.Kind.MAP) return null;

    const mapping = (currentNode as yamlAst.YamlMap).mappings.find(
      (m) => m.key.value === segment
    );
    if (!mapping) return null;

    currentNode = mapping.value;
    console.log(currentNode)
  }

  return currentNode;
}

function findInfoByPath(pathStr: string) {
  for (const [unit, fields] of Object.entries(settingsMap)) {
    for (const [key, props] of Object.entries(fields)) {
      if ((props as any)?.upstream_path === pathStr) {
        return props;
      }
    }
  }
  return null;
}

function createDecoration() {
  documentedDecoration = vscode.window.createTextEditorDecorationType({
    after: {
      contentText: '🟢 documented',
      color: '#5faf5f',
      margin: '0 0 0 1em',
    },
  });
}

export function deactivate() { }
