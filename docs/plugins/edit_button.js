const editButton = (hook, vm) => {
  hook.beforeEach(function (html) {
    let editButton = window.$docsify.editButton;
    let url = `https://github.com/${editButton.username}/${editButton.repoName}/tree/${editButton.branch}/${editButton.docsPath}/${vm.route.file}`;
    let editHtml = "[" + editButton.editText + "](" + url + ")";
    return editHtml + "<br/>\n" + html;
  });
};
window.$docsify.plugins.push(editButton);
