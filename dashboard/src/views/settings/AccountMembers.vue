<template>
	<Card
		title="Team Members"
		subtitle="Team members can access your account on your behalf."
	>
		<template #actions>
			<Button
				v-if="showManageTeamButton"
				@click="showManageMemberDialog = true"
			>
				Manage
			</Button>
		</template>
		<div class="max-h-96 divide-y">
			<ListItem
				v-for="member in $account.team_members"
				:title="`${member.first_name} ${member.last_name}`"
				:description="member.name"
				:key="member.name"
			>
				<template #actions>
					<Badge
						:label="getRoleBadgeProps(member).status"
						:colorMap="$badgeStatusColorMap"
					/>
				</template>
			</ListItem>
		</div>

		<Dialog
			:options="{ title: 'Manage Members' }"
			v-model="showManageMemberDialog"
		>
			<template v-slot:body-content>
				<ListItem
					v-for="member in $account.team_members"
					:title="`${member.first_name} ${member.last_name}`"
					:description="member.name"
					:key="member.name"
				>
					<template #actions>
						<Button
							v-if="getRoleBadgeProps(member).status == 'Member'"
							class="ml-2 p-4"
							@click="removeMember(member)"
							:loading="$resources.removeMember.loading"
						>
							Remove
						</Button>
						<Badge v-else v-bind="getRoleBadgeProps(member)" />
					</template>
				</ListItem>

				<div v-if="showAddMemberForm">
					<h5 class="mt-5 text-sm font-semibold">Add Member</h5>
					<Input
						label="Enter the email address of your teammate to invite them."
						type="text"
						class="mt-2"
						v-model="memberEmail"
						required
					/>
					<ErrorMessage :error="$resourceErrors" />

					<div class="mt-5 flex flex-row justify-end">
						<Button @click="showAddMemberForm = false"> Cancel </Button>
						<Button
							class="ml-2"
							appearance="primary"
							:loading="$resources.addMember.loading"
							@click="$resources.addMember.submit({ email: memberEmail })"
						>
							Send Invitation
						</Button>
					</div>
				</div>
				<div v-else class="mt-5 flex flex-row justify-end">
					<Button appearance="primary" @click="showAddMemberForm = true">
						Add Member
					</Button>
				</div>
			</template>
		</Dialog>
	</Card>
</template>
<script>
export default {
	name: 'AccountMembers',
	data() {
		return {
			showManageMemberDialog: false,
			showAddMemberForm: false,
			memberEmail: null
		};
	},
	resources: {
		addMember: {
			method: 'press.api.account.add_team_member',
			onSuccess() {
				this.showManageMemberDialog = false;
				this.memberEmail = null;
				this.$notify({
					title: 'Invite Sent!',
					message: 'They will receive an email shortly to join your team.',
					color: 'green',
					icon: 'check'
				});
			}
		},
		removeMember: {
			method: 'press.api.account.remove_team_member',
			onSuccess() {
				this.showManageMemberDialog = false;
				this.$account.fetchAccount();
				this.$notify({
					title: 'Team member removed.',
					icon: 'check',
					color: 'green'
				});
			}
		}
	},
	methods: {
		getRoleBadgeProps(member) {
			let role = 'Member';
			if (this.$account.team.name == member.name) {
				role = 'Owner';
			}

			return {
				status: role,
				color: {
					Owner: 'blue',
					Member: 'gray'
				}[role]
			};
		},
		removeMember(member) {
			this.$confirm({
				title: 'Remove Member',
				message: `Are you sure you want to remove ${member.first_name} ?`,
				actionLabel: 'Remove',
				action: closeDialog => {
					this.$resources.removeMember.submit({ user_email: member.name });
					closeDialog();
				}
			});
		}
	},
	computed: {
		showManageTeamButton() {
			const team = this.$account.team;
			let show = this.$account.hasRole('Press Admin');
			return (
				show &&
				(team.default_payment_method ||
					team.payment_mode == 'Prepaid Credits' ||
					team.free_account ||
					team.erpnext_partner)
			);
		}
	}
};
</script>
