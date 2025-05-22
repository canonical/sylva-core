// tools/vscode-units-extension/extension.ts
import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'yaml';
import * as yamlAst from 'yaml-ast-parser';

let settingsMap: Record<string, any> = {};
const rootPath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? "";
const config = vscode.workspace.getConfiguration('unitsExtension');
const settingsRelPath = config.get<string>('settingsPath') ?? 'charts/sylva-units/schemas/units-settings.yaml';
const valuesRelPath = config.get<string>('valuesPath') ?? 'charts/sylva-units/values.yaml';
const settingsPath = path.join(rootPath, settingsRelPath);
const valuesPath = path.join(rootPath, valuesRelPath);

let documentedDecoration: vscode.TextEditorDecorationType;
let documentedDecoration2: vscode.TextEditorDecorationType;

export function activate(context: vscode.ExtensionContext) {

  init()

  // Hover provider
  context.subscriptions.push(
    vscode.languages.registerHoverProvider('yaml', {
      provideHover(document, position) {
        if (!document.fileName.endsWith('values.yaml')) return;

        const wordRange = document.getWordRangeAtPosition(position, /[\w-]+/);
        const key = wordRange ? document.getText(wordRange) : '';
        if (!key) return;

        const linePrefix = document.lineAt(position.line).text.trim();
        if (!linePrefix.includes(key)) return;

        const matchedEntry = findEntryByFinalKey(key);
        if (matchedEntry) {
          const { description, example, upstream_path }: any = matchedEntry;
          return new vscode.Hover(
            `**${description || 'No description'}**\n\nExample: \`${example || '—'}\`\n\nInjected into: \`${upstream_path}\` (from units-settings.yaml)`
          );
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

        const targetNode = findNodeByPath(ast, keys);
        console.log("goto: ", pathStr)

        if (!targetNode) return;

        const startPos = valuesTextDocument.positionAt(targetNode.startPosition);
        return new vscode.Location(valuesTextDocument.uri, startPos);
      },
    })
  );

  context.subscriptions.push(
    vscode.workspace.onDidOpenTextDocument((event) => {
      if (event.fileName.endsWith('yaml')) {
        console.log("onDidOpenTextDocument: ", event)
        reloadSettings()
      }
    })
  );

  context.subscriptions.push(
    vscode.workspace.onDidChangeTextDocument((event) => {
      if (event.document.fileName.endsWith('yaml')) {
        console.log("onDidChangeTextDocument: ", event)
        reloadSettings()
      }
    })
  );

  context.subscriptions.push(
    vscode.window.onDidChangeActiveTextEditor((event) => {
      if (event?.document.fileName.includes('values.yaml')) {
        console.log("onDidChangeActiveTextEditor: ", event)
        reloadSettings()
        decorateDocumentedKeys(event?.document);
      }
    })
  );

}

function init() {
  try {
    const rawYaml = fs.readFileSync(settingsPath, 'utf-8');
    settingsMap = yaml.parse(rawYaml);
  } catch (err) {
    console.error('Failed to load units-settings.yaml:', err);
    return;
  }

  createDecoration()

  const activeDoc = vscode.window.activeTextEditor?.document;
  if (activeDoc?.fileName.endsWith('values.yaml')) {
    decorateDocumentedKeys(activeDoc);
  }
}

function reloadSettings() {
  try {
    const rawYaml = fs.readFileSync(settingsPath, 'utf-8');
    settingsMap = yaml.parse(rawYaml);
    console.log('settingsMap reloaded');
  } catch (err) {
    console.error('[UnitsExtension] Failed to reload settings:', err);
  }
}

async function decorateDocumentedKeys(doc: vscode.TextDocument) {
  const editor = vscode.window.visibleTextEditors.find(e => e.document.fileName === doc.fileName);
  if (!editor) return;

  const raw = doc.getText();
  const ast = yamlAst.load(raw);
  const decorations: vscode.DecorationOptions[] = [];

  for (const [_, fields] of Object.entries(settingsMap)) {
    for (const [_, props] of Object.entries(fields)) {
      const upstream = (props as any)?.upstream_path;
      if (typeof upstream !== 'string') continue;

      const pathSegments = upstream.replace(/^\./, '').split('.');
      const targetNode = findNodeByPath(ast, pathSegments);
      console.log("latest ast node: ", "decorating: ", targetNode?.value)
      if (!targetNode) {
        console.warn(`Could not find path in values.yaml:`, pathSegments.join('.'));
        continue
      }

      const line = doc.positionAt(targetNode.startPosition).line;
      const range = new vscode.Range(line, doc.lineAt(line).range.end.character, line, doc.lineAt(line).range.end.character);
      decorations.push({ range });
    }
  }

  for (const [unit, fields] of Object.entries(settingsMap)) {
    for (const [key, props] of Object.entries(fields)) {
      const upstream = (props as any)?.upstream_path;
      if (typeof upstream !== 'string') continue;

      const parts = upstream.replace(/^\./, '').split('.');
      const finalKey = parts[parts.length - 1];

      const regex = new RegExp(`\\.settings\\.${finalKey}\\b`, 'g');
      let match: RegExpExecArray | null;
      while ((match = regex.exec(raw)) !== null) {
        const start = doc.positionAt(match.index);
        const end = doc.positionAt(match.index + match[0].length);
        decorations.push({ range: new vscode.Range(start, end) });
      }
    }
  }

  editor.setDecorations(documentedDecoration, decorations);
  editor.setDecorations(documentedDecoration2, decorations);
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
  }
  // console.log("latest ast node:", currentNode)
  return currentNode;
}

function findEntryByFinalKey(finalKey: string) {
  for (const unit of Object.values(settingsMap)) {
    for (const [key, props] of Object.entries(unit)) {
      if (key === finalKey) {
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

  documentedDecoration2 = vscode.window.createTextEditorDecorationType({
    color: '#5faf5f',
    fontWeight: 'bold',
    border: '1px solid #5faf5f',
    borderRadius: '2px',
  });
}

export function deactivate() { }
