<template>
	<div>
		<div v-if="site">
			<div class="pb-2">
				<div class="text-base text-gray-700">
					<router-link to="/sites" class="hover:text-gray-800">
						← Back to Sites
					</router-link>
				</div>
				<div
					class="flex flex-col space-y-3 md:flex-row md:items-baseline md:justify-between md:space-y-0"
				>
					<div class="mt-2 flex items-center">
						<h1 class="text-2xl font-bold">
							{{ site.host_name || site.name }}
						</h1>
						<Badge
							class="ml-4 hidden md:inline-block"
							:label="site.status"
							:colorMap="$badgeStatusColorMap"
						/>

						<div
							v-if="regionInfo"
							class="ml-2 hidden cursor-default flex-row items-center self-end rounded-md bg-yellow-50 px-3 py-1 text-xs font-medium text-yellow-700 md:flex"
						>
							<img
								v-if="regionInfo.image"
								class="mr-2 h-4"
								:src="regionInfo.image"
								:alt="`Flag of ${regionInfo.title}`"
								:title="regionInfo.image"
							/>
							<p>{{ regionInfo.title }}</p>
						</div>
					</div>
					<div class="mb-10 flex flex-row justify-between md:hidden">
						<div class="flex flex-row">
							<Badge :label="site.status" :colorMap="$badgeStatusColorMap" />
							<div
								v-if="regionInfo"
								class="ml-2 flex cursor-default flex-row items-center rounded-md bg-yellow-50 px-3 py-1 text-xs font-medium text-yellow-700"
							>
								<img
									v-if="regionInfo.image"
									class="mr-2 h-4"
									:src="regionInfo.image"
									:alt="`Flag of ${regionInfo.title}`"
									:title="regionInfo.image"
								/>
								<p>{{ regionInfo.title }}</p>
							</div>
						</div>

						<!-- Only for mobile view -->
						<Dropdown
							v-if="siteActions.length > 0"
							:options="siteActions"
							right
						>
							<template v-slot="{ open }">
								<Button icon-right="chevron-down">Actions</Button>
							</template>
						</Dropdown>
					</div>

					<div class="hidden flex-row space-x-3 md:flex">
						<Button
							v-for="action in siteActions"
							v-if="siteActions.length <= 2"
							:key="action.label"
							:icon-left="action.icon"
							:loading="action.loading"
							:route="action.route"
							@click="action.handler"
						>
							{{ action.label }}
						</Button>

						<Dropdown v-if="siteActions.length > 2" :options="siteActions">
							<template v-slot="{ open }">
								<Button icon-right="chevron-down">Actions</Button>
							</template>
						</Dropdown>
					</div>
				</div>
			</div>
		</div>
		<div>
			<Tabs :tabs="tabs">
				<router-view v-slot="{ Component, route }">
					<component v-if="site" :is="Component" :site="site"></component>
				</router-view>
			</Tabs>
		</div>

		<Dialog
			:options="{ title: 'Login As Administrator' }"
			v-model="showReasonForAdminLoginDialog"
		>
			<template v-slot:body-content>
				<Input
					label="Reason for logging in as Administrator"
					type="textarea"
					v-model="reasonForAdminLogin"
					required
				/>

				<ErrorMessage class="mt-3" :error="errorMessage" />
			</template>

			<template #actions>
				<Button
					:loading="$resources.loginAsAdmin.loading"
					@click="proceedWithLoginAsAdmin"
					appearance="primary"
					>Proceed</Button
				>
			</template>
		</Dialog>
	</div>
</template>

<script>
import Tabs from '@/components/Tabs.vue';
import { loginAsAdmin } from '@/controllers/loginAsAdmin';

export default {
	name: 'Site',
	pageMeta() {
		return {
			title: `Site - ${this.siteName} - Frappe Cloud`
		};
	},
	props: ['siteName'],
	components: {
		Tabs
	},
	data() {
		return {
			runningJob: false,
			reasonForAdminLogin: '',
			showReasonForAdminLoginDialog: false,
			errorMessage: ''
		};
	},
	resources: {
		site() {
			return {
				method: 'press.api.site.get',
				params: {
					name: this.siteName
				},
				auto: true,
				onSuccess() {
					if (this.siteName !== this.site.name) {
						this.$router.replace({ params: { siteName: this.site.name } });
					}
					if (this.site.status !== 'Active' || this.site.setup_wizard_complete)
						return;

					this.$call('press.api.site.setup_wizard_complete', {
						name: this.siteName
					})
						.then(complete => {
							this.site.setup_wizard_complete = Boolean(complete);
						})
						.catch(() => (this.site.setup_wizard_complete = false));
				},
				onError: this.$routeTo404PageIfNotFound
			};
		},
		loginAsAdmin() {
			return loginAsAdmin(this.siteName);
		}
	},
	activated() {
		this.setupAgentJobUpdate();
		if (this.site) {
			this.routeToGeneral();
		} else {
			this.$resources.site.once('onSuccess', () => {
				this.routeToGeneral();
			});
		}

		if (this.site?.status === 'Active') {
			this.$socket.on('list_update', this.onSocketUpdate);
		}
	},
	deactivated() {
		this.$socket.off('list_update', this.onSocketUpdate);
	},
	methods: {
		onSocketUpdate({ doctype, name }) {
			if (doctype === 'Site' && name === this.siteName) {
				this.$resources.site.reload();
			}
		},
		setupAgentJobUpdate() {
			if (this._agentJobUpdateSet) return;
			this._agentJobUpdateSet = true;

			this.$socket.on('agent_job_update', data => {
				if (data.name === 'New Site' || data.name === 'New Site from Backup') {
					if (data.status === 'Success' && data.site === this.siteName) {
						setTimeout(() => {
							// running reload immediately doesn't work for some reason
							this.$router.push(`/sites/${this.siteName}/overview`);
							this.$resources.site.reload();
						}, 1000);
					}
				}
				this.runningJob =
					data.site === this.siteName && data.status !== 'Success';
			});
		},
		routeToGeneral() {
			if (this.$route.matched.length === 1) {
				let tab = ['Pending', 'Installing'].includes(this.site.status)
					? 'jobs'
					: 'overview';
				this.$router.replace(`/sites/${this.site.name}/${tab}`);
			}
		},
		proceedWithLoginAsAdmin() {
			this.errorMessage = '';

			if (!this.reasonForAdminLogin.trim()) {
				// The input is empty
				this.errorMessage = 'Reason is required';
				return;
			}

			this.$resources.loginAsAdmin.submit({
				name: this.siteName,
				reason: this.reasonForAdminLogin
			});

			this.showReasonForAdminLoginDialog = false;
		}
	},
	computed: {
		site() {
			return this.$resources.site.data;
		},

		regionInfo() {
			if (!this.$resources.site.loading && this.$resources.site.data) {
				return this.$resources.site.data.server_region_info;
			}
		},

		siteActions() {
			return [
				['Active', 'Updating'].includes(this.site.status) && {
					label: 'Visit Site',
					icon: 'external-link',
					handler: () => {
						window.open(`https://${this.site.name}`, '_blank');
					}
				},
				this.$account.user.user_type == 'System User' && {
					label: 'View in Desk',
					icon: 'external-link',
					handler: () => {
						window.open(
							`${window.location.protocol}//${window.location.host}/app/site/${this.site.name}`,
							'_blank'
						);
					}
				},
				this.site.group && {
					label: 'Manage Bench',
					icon: 'tool',
					route: `/benches/${this.site.group}`,
					handler: () => {
						this.$router.push(`/benches/${this.site.group}`);
					}
				},
				this.site.status == 'Active' && {
					label: 'Login As Administrator',
					icon: 'external-link',
					loading: this.$resources.loginAsAdmin.loading,
					handler: () => {
						if (this.$account.team.name == this.site.team) {
							return this.$resources.loginAsAdmin.submit({
								name: this.siteName
							});
						}

						this.showReasonForAdminLoginDialog = true;
					}
				},
				this.$account.user.user_type == 'System User' && {
					label: 'Impersonate Team',
					icon: 'tool',
					handler: async () => {
						await this.$account.switchTeam(this.site.team);
						this.$notify({
							title: 'Switched Team',
							message: `Switched to ${this.site.team}`,
							icon: 'check',
							color: 'green'
						});
					}
				}
			].filter(Boolean);
		},

		tabs() {
			let siteConfig = '';
			let tabRoute = subRoute => `/sites/${this.siteName}/${subRoute}`;
			let tabs = [
				{ label: 'Overview', route: 'overview' },
				{ label: 'Apps', route: 'apps' },
				{ label: 'Analytics', route: 'analytics' },
				{ label: 'Database', route: 'database' },
				{ label: 'Site Config', route: 'site-config' },
				{ label: 'Jobs', route: 'jobs', showRedDot: this.runningJob },
				{ label: 'Logs', route: 'logs' }
			];

			if (this.site && this.site.hide_config !== 1) {
				siteConfig = 'Site Config';
			}

			let tabsByStatus = {
				Active: [
					'Overview',
					'Apps',
					'Analytics',
					'Database',
					siteConfig,
					'Jobs',
					'Logs',
					'Request Logs'
				],
				Inactive: ['Overview', 'Apps', 'Database', siteConfig, 'Jobs', 'Logs'],
				Installing: ['Jobs'],
				Pending: ['Jobs'],
				Broken: ['Overview', 'Apps', siteConfig, 'Database', 'Jobs', 'Logs'],
				Suspended: ['Overview', 'Apps', 'Database', 'Jobs', 'Plan']
			};
			if (this.site) {
				let tabsToShow = tabsByStatus[this.site.status];
				if (tabsToShow?.length) {
					tabs = tabs.filter(tab => tabsToShow.includes(tab.label));
				}
				return tabs.map(tab => {
					return {
						...tab,
						route: tabRoute(tab.route)
					};
				});
			}
			return [];
		}
	}
};
</script>
