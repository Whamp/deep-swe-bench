import '../node_modules/@pierre/diffs/dist/components/web-components.js';
import { FileDiff } from '@pierre/diffs';
import { currentPrompt, proposedPrompt } from './prompts.js';
import './style.css';

const container = document.querySelector('#prompt-diff');
const buttons = [...document.querySelectorAll('[data-view]')];
const oldFile = {
  name: 'current-v1.txt',
  contents: currentPrompt,
  lang: 'text',
};
const newFile = {
  name: 'proposed-v2.txt',
  contents: proposedPrompt,
  lang: 'text',
};

let view = window.matchMedia('(max-width: 720px)').matches
  ? 'unified'
  : 'split';

const baseOptions = {
  diffIndicators: 'bars',
  lineDiffType: 'word',
  overflow: 'wrap',
  expandUnchanged: true,
  disableFileHeader: true,
  themeType: 'light',
  unsafeCSS: `
    [data-code] { font-size: 14px; line-height: 1.62; }
    [data-line] { min-height: 2.8rem; }
  `,
};
const diff = new FileDiff({ ...baseOptions, diffStyle: view });

function updateButtons() {
  for (const button of buttons) {
    button.setAttribute(
      'aria-pressed',
      String(button.dataset.view === view),
    );
  }
  document.body.dataset.view = view;
}

function render() {
  diff.setOptions({ ...baseOptions, diffStyle: view });
  diff.render({ oldFile, newFile, containerWrapper: container, forceRender: true });
  updateButtons();
}

for (const button of buttons) {
  button.addEventListener('click', () => {
    view = button.dataset.view;
    render();
  });
}

render();
