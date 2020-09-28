const editButton = (hook, vm) => {
  hook.beforeEach(function (html) {
    let editButton = window.$docsify.editButton;
    let url = `https://github.com/${editButton.username}/${editButton.repoName}/tree/${editButton.branch}/${vm.route.file}`;
    let editHtml = "[📝 EDIT DOCUMENT](" + url + ")";
    axios
      .get(
        `https://api.github.com/repos/${editButton.username}/${editButton.repoName}/commits?path=${vm.route.file}&page=1&per_page=1`
      )
      .then(function (response) {
        let time = response.data[0].commit.committer.date;
        let formatTime = moment(time, "YYYYMMDD").startOf("hour").fromNow();
        document
          .querySelector(".content article p a")
          .insertAdjacentHTML("afterend", `<div>Last modified ${formatTime}</div>`);
      })
      .catch(function (error) {
        console.log(error);
      });
    return editHtml + "\n\n" + html;
  });
};
window.$docsify.plugins.push(editButton);
