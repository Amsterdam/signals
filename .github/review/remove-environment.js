const { Octokit } = require("@octokit/action");

const [owner, repo] = process.env.GITHUB_REPOSITORY.split("/");
const environmentName = process.env.ENVIRONMENT_NAME;

removeEnvironment(environmentName);

async function removeEnvironment(environmentName) {
    const octokit = new Octokit();

    try {
        const { data } = await octokit.request(
            "DELETE /repos/{owner}/{repo}/environments/{environmentName}", {
                owner,
                repo,
                environmentName,
            }
        )

        console.log("Removed environment", data);
    } catch (error) {
        console.error('Error while deleting', error);
    }
}
